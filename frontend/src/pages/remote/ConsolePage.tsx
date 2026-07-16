import { useCallback, useEffect, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { Terminal } from "@xterm/xterm";
import { FitAddon } from "@xterm/addon-fit";
import "@xterm/xterm/css/xterm.css";
import PageHeader from "../../components/common/PageHeader";
import { useToast } from "../../contexts/ToastContext";
import { hostsApi, HostData } from "../../services/remote";

export default function ConsolePage() {
    const { showToast } = useToast();
    const [searchParams] = useSearchParams();
    const [hosts, setHosts] = useState<HostData[]>([]);
    const [selectedHostId, setSelectedHostId] = useState<number | "">(
        () => Number(searchParams.get("host_id")) || "",
    );
    const [connected, setConnected] = useState(false);
    const [connecting, setConnecting] = useState(false);
    const termRef = useRef<HTMLDivElement>(null);
    const termInstance = useRef<Terminal | null>(null);
    const fitAddon = useRef<FitAddon | null>(null);
    const wsRef = useRef<WebSocket | null>(null);

    useEffect(() => {
        hostsApi.list().then((d) => setHosts(d.items)).catch(() => {});
    }, []);

    useEffect(() => {
        if (!termRef.current) return;
        const term = new Terminal({
            cursorBlink: true,
            fontSize: 14,
            fontFamily: "monospace",
            theme: {
                background: "#1a1b26",
                foreground: "#a9b1d6",
                cursor: "#c0caf5",
                selectionBackground: "#33467c",
            },
        });
        const fit = new FitAddon();
        term.loadAddon(fit);
        term.open(termRef.current);
        fit.fit();
        termInstance.current = term;
        fitAddon.current = fit;

        const onResize = () => fit.fit();
        window.addEventListener("resize", onResize);

        return () => {
            window.removeEventListener("resize", onResize);
            term.dispose();
            termInstance.current = null;
        };
    }, []);

    const handleConnect = useCallback(() => {
        if (!selectedHostId || connected) return;

        setConnecting(true);
        const term = termInstance.current;
        if (!term) return;

        term.clear();
        term.writeln("Connecting...");

        const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
        const host = hosts.find((h) => h.id === selectedHostId);
        const ws = new WebSocket(
            `${proto}//${window.location.host}/api/v1/remote/console?host_id=${selectedHostId}`,
        );
        wsRef.current = ws;

        ws.onopen = () => {};

        ws.onmessage = (ev) => {
            const msg = JSON.parse(ev.data);
            if (msg.type === "connected") {
                setConnected(true);
                setConnecting(false);
                term.clear();
                term.focus();
                if (fitAddon.current) fitAddon.current.fit();
                if (ws.readyState === WebSocket.OPEN) {
                    ws.send(JSON.stringify({
                        type: "resize",
                        width: term.cols,
                        height: term.rows,
                    }));
                }
            } else if (msg.type === "output") {
                term.write(msg.data);
            } else if (msg.type === "exit") {
                term.writeln(`\r\n[Process exited with code ${msg.exit_code}]`);
                setConnected(false);
            } else if (msg.type === "error") {
                term.writeln(`\r\n[Error: ${msg.message}]`);
                setConnected(false);
                setConnecting(false);
            }
        };

        ws.onclose = () => {
            if (!connected) {
                term.writeln("\r\n[Connection closed]");
            }
            setConnected(false);
            setConnecting(false);
            wsRef.current = null;
        };

        ws.onerror = () => {
            setConnecting(false);
            setConnected(false);
        };

        term.onData((data) => {
            if (ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({ type: "input", data }));
            }
        });

        const resizeHandler = () => {
            if (fitAddon.current) fitAddon.current.fit();
            if (ws.readyState === WebSocket.OPEN) {
                ws.send(
                    JSON.stringify({
                        type: "resize",
                        width: term.cols,
                        height: term.rows,
                    }),
                );
            }
        };
        window.addEventListener("resize", resizeHandler);
    }, [selectedHostId, connected, hosts]);

    const handleDisconnect = useCallback(() => {
        wsRef.current?.close();
        setConnected(false);
    }, []);

    useEffect(() => {
        return () => {
            wsRef.current?.close();
        };
    }, []);

    return (
        <>
            <PageHeader
                title="Interactive Console"
                subtitle="SSH terminal session — type commands directly"
            />
            <div className="execute-form">
                <div className="form-row">
                    <label className="form-label">Host</label>
                    <select
                        className="form-select"
                        value={selectedHostId}
                        onChange={(e) => {
                            const val = Number(e.target.value) || "";
                            setSelectedHostId(val);
                            if (connected) handleDisconnect();
                        }}
                        disabled={connected}
                    >
                        <option value="">Select a host…</option>
                        {hosts.map((h) => (
                            <option key={h.id} value={h.id}>
                                {h.name} ({h.hostname})
                            </option>
                        ))}
                    </select>
                    {!connected ? (
                        <button
                            className="btn btn-primary"
                            onClick={handleConnect}
                            disabled={connecting || !selectedHostId}
                        >
                            {connecting ? "Connecting…" : "Connect"}
                        </button>
                    ) : (
                        <button
                            className="btn btn-danger"
                            onClick={handleDisconnect}
                        >
                            Disconnect
                        </button>
                    )}
                </div>
            </div>
            <div className="console-terminal-wrapper">
                <div ref={termRef} className="console-terminal" />
            </div>
        </>
    );
}
