import { useState, useEffect } from "react";

export default function StatusBar() {
    const [time, setTime] = useState(() => new Date());

    useEffect(() => {
        const timer = setInterval(() => setTime(new Date()), 1000);
        return () => clearInterval(timer);
    }, []);

    return (
        <footer className="statusbar">
            <div className="statusbar-left">
                <span className="statusbar-item">
                    <span className="statusbar-dot green" />
                    Connected
                </span>
            </div>
            <div className="statusbar-right">
                <span className="statusbar-item">
                    {time.toLocaleTimeString()}
                </span>
            </div>
        </footer>
    );
}
