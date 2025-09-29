import { NextApiRequest, NextApiResponse } from 'next';
import axios from 'axios';

const OPENAI_API_KEY = process.env.OPENAI_API_KEY;
const ANTHROPIC_API_KEY = process.env.ANTHROPIC_API_KEY;
const GROQ_API_KEY = process.env.GROQ_API_KEY;

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  const { provider, prompt } = req.body;

  try {
    let response;

    switch (provider) {
      case 'openai':
        response = await axios.post('https://api.openai.com/v1/chat/completions', {
          messages: [{ role: 'user', content: prompt }],
        }, {
          headers: {
            'Authorization': `Bearer ${OPENAI_API_KEY}`,
            'Content-Type': 'application/json',
          },
        });
        break;
      case 'anthropic':
        response = await axios.post('https://api.anthropic.com/v1/complete', {
          prompt: prompt,
          max_tokens: 150,
        }, {
          headers: {
            'Authorization': `Bearer ${ANTHROPIC_API_KEY}`,
          },
        });
        break;
      case 'groq':
        response = await axios.post('https://api.groq.com/v1/generate', {
          input: prompt,
        }, {
          headers: {
            'Authorization': `Bearer ${GROQ_API_KEY}`,
          },
        });
        break;
      default:
        return res.status(400).json({ error: 'Invalid provider' });
    }

    return res.status(200).json(response.data);
  } catch (error) {
    return res.status(500).json({ error: error.message });
  }
}