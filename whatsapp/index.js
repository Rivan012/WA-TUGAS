const axios = require("axios");
const {
    default: makeWASocket,
    useMultiFileAuthState,
    DisconnectReason
} = require("@whiskeysockets/baileys");
const express = require("express");

const app = express();

app.use(express.json());
const qrcode = require("qrcode-terminal");

async function startBot() {
    const { state, saveCreds } = await useMultiFileAuthState("./auth");

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

        const text =
            msg.message.conversation ||
            msg.message.extendedTextMessage?.text ||
            "";

        console.log("=======================");
        console.log("From :", from);
        console.log("Text :", text);
        console.log("=======================");

        try {

            const response = await axios.post(
                "http://127.0.0.1:8000/webhook",
                {
                    from_number: from,
                    message: text
                }
            );

            await sock.sendMessage(from, {
                text: response.data.reply
            });

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

            console.log("BERHASIL");
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