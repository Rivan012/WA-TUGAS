const axios = require("axios");
const path = require("path");
const {
    default: makeWASocket,
    useMultiFileAuthState,
    DisconnectReason
} = require("@whiskeysockets/baileys");
const express = require("express");

const app = express();

app.use(express.json());
const qrcode = require("qrcode-terminal");

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8000";

// Cache nama grup biar gak nge-hit sock.groupMetadata() tiap ada pesan masuk
// (network call ke server WA tiap kali bisa lambat/kena rate limit).
const groupNameCache = new Map(); // jid -> { name, fetchedAt }
const GROUP_NAME_TTL_MS = 10 * 60 * 1000; // 10 menit

async function getGroupName(sock, jid) {
    const cached = groupNameCache.get(jid);
    if (cached && Date.now() - cached.fetchedAt < GROUP_NAME_TTL_MS) {
        return cached.name;
    }
    try {
        const meta = await sock.groupMetadata(jid);
        groupNameCache.set(jid, { name: meta.subject, fetchedAt: Date.now() });
        return meta.subject;
    } catch (e) {
        return cached ? cached.name : null;
    }
}

// Ambil bagian nomor dari JID, buang device-id (":12") dan domain (@s.whatsapp.net / @lid),
// supaya bisa dibandingkan apple-to-apple.
function jidNumber(jid) {
    if (!jid) return null;
    return jid.split("@")[0].split(":")[0];
}

// Hapus token mention literal ("@62812xxxxxxx") dari teks pesan grup,
// biar sisa teksnya bersih buat dicek sebagai perintah (/tambah, /list, dst).
function stripMentions(text) {
    return text.replace(/@\d+\s*/g, "").trim();
}

async function startBot() {
    const { state, saveCreds } = await useMultiFileAuthState(
        path.join(__dirname, "auth")
    );

    const sock = makeWASocket({
        auth: state
    });

    sock.ev.on("creds.update", saveCreds);

    sock.ev.on("connection.update", ({ connection, lastDisconnect, qr }) => {

        if (qr) {
            qrcode.generate(qr, { small: true });
        }

        if (connection === "open") {
            console.log("✅ WhatsApp Connected");
            console.log("Logged in as:", sock.user?.id);
        }

        if (connection === "close") {
            const shouldReconnect =
                lastDisconnect?.error?.output?.statusCode !== DisconnectReason.loggedOut;

            console.log("❌ Connection closed");

            if (shouldReconnect) {
                console.log("🔄 Reconnecting...");
                startBot();
            }
        }
    });

    sock.ev.on("messages.upsert", async ({ messages }) => {

        const msg = messages[0];

        if (!msg.message) return;
        if (msg.key.fromMe) return;

        const from = msg.key.remoteJid;
        const isGroup = from?.endsWith("@g.us");

        const extText = msg.message.extendedTextMessage;
        const rawText = msg.message.conversation || extText?.text || "";

        // Identitas pengirim asli: di grup, remoteJid adalah JID grup, jadi
        // pengirim sebenarnya ada di key.participant. Di chat pribadi, sama dengan `from`.
        const senderId = isGroup ? (msg.key.participant || from) : from;

        let isMentioned = true; // default: chat pribadi selalu dianggap "boleh diproses"
        let groupName = null;
        let text = rawText;

        if (isGroup) {
            const mentioned = extText?.contextInfo?.mentionedJid || [];

            // Bot bisa di-tag pakai dua identitas berbeda: nomor telepon biasa
            // (@s.whatsapp.net) ATAU LID (@lid) — WhatsApp sekarang lebih sering
            // pakai LID untuk mention, jadi harus dicocokkan ke keduanya.
            const botNumber = jidNumber(sock.user?.id);
            const botLid = jidNumber(sock.user?.lid);

            isMentioned = mentioned.some((j) => {
                const n = jidNumber(j);
                return n === botNumber || n === botLid;
            });
            text = stripMentions(rawText);

            groupName = await getGroupName(sock, from);

            // Lapor ke backend supaya grup ini muncul di dashboard (kalau belum terdaftar).
            // Dikirim untuk semua pesan grup (bukan cuma yang nge-tag), biar grup baru
            // langsung kedeteksi walau anggotanya belum pernah tag bot.
            axios
                .post(`${BACKEND_URL}/webhook/group-seen`, {
                    group_id: from,
                    group_name: groupName,
                })
                .catch((e) => console.error("Gagal lapor group-seen:", e.message));
        }

        console.log("=======================");
        console.log("From      :", from, isGroup ? `(grup: ${groupName})` : "(pribadi)");
        console.log("Sender    :", senderId);
        console.log("Text      :", text);
        console.log("Mentioned :", isMentioned);
        console.log("=======================");

        try {

            const response = await axios.post(`${BACKEND_URL}/webhook`, {
                from_number: senderId,
                message: text,
                chat_id: from,
                is_group: !!isGroup,
                group_id: isGroup ? from : null,
                group_name: groupName,
                is_mentioned: isMentioned,
            });

            const reply = response.data?.reply;

            // reply === null artinya backend sengaja diam (grup belum terdaftar / gak di-tag)
            if (reply) {
                await sock.sendMessage(from, { text: reply });
            }

        } catch (err) {

            console.error("Backend Error:");

            if (err.response) {
                console.log(err.response.status);
                console.log(err.response.data);
            } else {
                console.log(err.message);
            }

            await sock.sendMessage(from, {
                text: "❌ Backend sedang offline"
            });

        }

    });
    app.post("/send-message", async (req, res) => {
        try {
            const { to, message } = req.body;

            // Normalisasi ke format JID WhatsApp
            let jid = to;
            if (!jid.includes("@")) {
                jid = jid.replace(/\D/g, ""); // buang karakter non-digit
                jid = `${jid}@s.whatsapp.net`;
            }

            console.log("Mengirim ke :", jid);

            await sock.sendMessage(jid, { text: message });

            console.log("BERHASIL");``
            res.json({ success: true });

        } catch (e) {
            console.log("ERROR", e);
            res.status(500).json({ success: false, error: e.message });
        }
    });
}

// ✅ CRITICAL FIX: Start the Express server
app.listen(3000, () => {
    console.log("🚀 Express API listening on http://127.0.0.1:3000");
});

startBot();