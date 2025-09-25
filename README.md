# ws-backpressure-starter This project demonstrates a credit-based WebSocket backpressure system with rolling cached snapshots. It provides a foundational real-time data stream architecture for high-performance applications. ## Project Structure - `server/`: Node.js and TypeScript WebSocket server - Implements credit-based flow control. - Utilizes a non-blocking rolling snapshot cache (500ms interval). - Simulates a stream of deltas. - `client/`: Vite and TypeScript web client - Connects to the WebSocket server. - Implements client-side credit management and message draining. - Provides a simple UI to visualize stream statistics and test backpressure (pause/resume). ## Quickstart ### 1. Clone the repository ```bash # This step is already done since you've created files locally and committed # git clone <YOUR_REPO_URL> # cd ws-backpressure-starter 2. Setup and Run the Server

Navigate to the server directory, install dependencies, and start the server.

cd server npm install npm run dev

The server will start on ws://localhost:8080/stream.

3. Setup and Run the Client

In a separate terminal, navigate to the client directory, install dependencies, and start the client.

cd ../client npm install npm run dev

Open the provided local URL in your browser (e.g., http://localhost:5173).

Verification

In the client UI:

Observe the streaming tickId, queue length, credits, count, snapshots applied, and deltas applied KPIs.Click Pause Drain to simulate a stalled client or a hidden browser tab.We should see the queue length grow as the server continues to send messages.The tickId will advance approximately every 500ms as the cached snapshot updates, demonstrating non-blocking snapshot delivery.Click Resume Drain to observe the client rapidly catching up on the queued messages.Next Steps

This starter project provides a robust foundation. Future enhancements could include:

Integrating actual graph data (nodes and edges) into the stream and snapshot.Developing the instanced renderer on the client-side using libraries like Pixi.js.Implementing worker threads and manifest-based snapshots for very large states.Adding comprehensive metrics and health endpoints. I will now provide the content for the server-side files.