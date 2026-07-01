"use client";
import { io, Socket } from "socket.io-client";

import { SOCKET_URL } from "./config";

let socket: Socket | null = null;

export function getSocket(): Socket {
  if (!socket) {
    socket = io(SOCKET_URL, { transports: ["websocket", "polling"] });
  }
  return socket;
}

export function subscribe(role: string, accountId: string | null) {
  const s = getSocket();
  const send = () => s.emit("subscribe", { role, account_id: accountId });
  if (s.connected) send();
  else s.on("connect", send);
}
