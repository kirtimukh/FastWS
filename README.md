# Websocket connections and pubsub applications

## App showcases pubsub in a simple fastapi app

[![Demo video](Link to demo video)](https://github.com/user-attachments/assets/e9fa4af9-c5dd-40d2-b6d7-009bc9df5b2b)

### In the video:
Docker runs **FastAPI app with 4 workers** in 1 container and a **redis service** in another.

The UI provides **4 ways to send message** to the server.
1. **http-out, http-in**
2. websockets, **ws-out, ws-in**: works all the time because the client and the server instance are connected via the websocket **connection throughout** the session
3. Makes http requests to server to **echo back the text through WS**. ws message **not guaranteed** because any instance may receive this request.
  -- [See 00:07 vs 00:16 of the video]
  -- [other options](#other-options)
4. Makes http requests to server to **publish text to redis**, all the workers subscribe to it, **echo text is guaranteed**.

### Setup:
1. [Install docker](https://docs.docker.com/desktop/)
2. `cd FastWS`
3. `docker compose up`

## WS connections are long lived

**HTTP connections are ephemereal** whereas **WebSocket connections are long lived**.
- **Once the request response cycle is over the server ends the connection with the client**. This is what allows web-applications to scale so well. It is possible to run multiple instances of the same application code and the app will do its job regardless of which instance receives your http request.
- **Websockets** connections are meant to **maintain connection for extended duration**. Thats why when **Client_A** connects with **Server_1** the connection is **kept alive in-memory** of **Server_1**.
- If **Server_10** receives an event that requires it to send the data to **Client_A**
  - it has to publish it to a **redis-like pubsub system**.
  - Similarly, it subscribes to the same queue for messages to clients whose WS-Connection it has in memory.

![illustration of pubsub](assets/pubsub.png)

## Other options

No options.

- **Nginx offers sticky connections based on the ip address, cookie, or header**: All http requests with an ip address are routed to the same server.
  - The custom cookie or header have to manually added.
  - This does not work with multiple workers, only with different containers
  - Cannot send server generated messages via websockets - have to use a pubsub system like Redis
- **Traefic can automatically generate sticky cookies**
  - But the problem of server generated messages persists.

Just do it like any other websocket app does, **USE PUBSUB**.

## Scaling

- Maintain **multiple websocket-only servers** across geographies
- **On initial connection - redirect** the user to make connection with the nearest ws-conn handlers
- Maintain a `user:server` map in a quick access memory (like redis), additionally distribute sections of it across different regions
- **Use dedicated queues** for dedicated servers
- **Watch** [popular geographies,queues,routes,servers] **and refine** [distribution of servers, queues, and client:server mapping] the above as your traffic grows and solidifies.
