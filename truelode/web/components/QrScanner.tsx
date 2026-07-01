"use client";
import { useEffect, useRef } from "react";

// Camera QR scanner. Calls onResult with the decoded text, then stops.
export default function QrScanner({
  onResult,
  onClose,
}: {
  onResult: (text: string) => void;
  onClose: () => void;
}) {
  const startedRef = useRef(false);

  useEffect(() => {
    let scanner: any;
    let cancelled = false;
    import("html5-qrcode").then(({ Html5Qrcode }) => {
      if (cancelled) return;
      scanner = new Html5Qrcode("qr-reader");
      startedRef.current = true;
      scanner
        .start(
          { facingMode: "environment" },
          { fps: 10, qrbox: 220 },
          (text: string) => {
            scanner.stop().catch(() => {});
            onResult(text);
          },
          () => {}
        )
        .catch((e: any) => onResult(`__error__${e}`));
    });
    return () => {
      cancelled = true;
      if (scanner && startedRef.current) scanner.stop().catch(() => {});
    };
  }, [onResult]);

  return (
    <div className="card" style={{ background: "#0d1319" }}>
      <div id="qr-reader" style={{ width: "100%", maxWidth: 320 }} />
      <button className="ghost" style={{ marginTop: 10 }} onClick={onClose}>
        Cancel scan
      </button>
    </div>
  );
}
