const BACKENDS = [
  "https://koyeb-backend-url",
  "https://render-backend-url"
];

export default async function handler(req, res) {
  const token = req.query.token;
  if (!token) {
    return res.status(400).send("Invalid link");
  }

  for (const backend of BACKENDS) {
    try {
      return res.redirect(302, `${backend}/download/${token}`);
    } catch (e) {}
  }

  res.status(503).send("All servers down.");
}
