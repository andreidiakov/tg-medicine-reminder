const functions = require("firebase-functions");
const express = require('express');

const app = express();

const buildXML = (text) => {
    return `<?xml version="1.0" encoding="UTF-8"?><Response>\
                <Say voice="alice" language="ru-RU">${text}</Say>\
            </Response>`;
};

app.post('/:text', (req, res) => {
    let message = req.params.text;
    message = buildXML(message);

    functions.logger.info(message, {structuredData: true});

    res.writeHead(200, {"Content-Type": "text/xml"});
    res.end(message);
});

exports.getXML = functions.https.onRequest(app);
