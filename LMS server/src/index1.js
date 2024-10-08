const express = require('express');
const { LMStudioClient } = require("@lmstudio/sdk");

const app = express();
app.use(express.json());

app.post('/predict', async (req, res) => {
  try {
    const client = new LMStudioClient();
    const model = await client.llm.load("monal04/llama-2-7b-chat.Q4_0.gguf-GGML-llama-2-7b-chat.Q4_0.gguf");

    const question = req.body.question;
    if (!question) {
      res.status(400).send({ error: 'No question provided' });
      return;
    }

    const prediction = model.respond([
      { role:'system', content: 'You are a helpful AI assistant.' },
      { role: 'user', content: question },
    ]);

    let responseText = '';
    for await (const text of prediction) {
      responseText += text;
    }

    res.send(responseText);
  } catch (error) {
    console.error('Error generating answer:', error);
    res.status(500).send({ error: 'Internal Server Error' });
  }
});

const port = 3000;
app.listen(port, () => {
  console.log(`Server listening on port ${port}`);
});