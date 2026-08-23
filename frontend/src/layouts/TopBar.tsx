import { useLocation, useNavigate } from "react-router-dom";
import Breadcrumb from "./Breadcrumb";
import { useState } from "react";

export default function TopBar() {
    const location = useLocation();
    const navigate = useNavigate();
    const [helpOpen, setHelpOpen] = useState(false);

    return (
        <header className="topbar">
            <Breadcrumb path={location.pathname} />
            <div className="topbar-actions">
                <input
                    className="topbar-search"
                    type="text"
                    placeholder="Search… (Ctrl+K)"
                    onKeyDown={(e) => {
                        if (e.key === "Escape") (e.target as HTMLInputElement).blur();
                    }}
                />
                <div className="topbar-help">
                    <button
                        className="topbar-help-toggle"
                        onClick={() => setHelpOpen((v) => !v)}
                        aria-label="Help"
                        title="Help"
                    >
                        ?
                    </button>
                    {helpOpen && (
                        <div className="topbar-help-menu">
                            <div className="topbar-help-title">Agent Bundle Downloads</div>
                            <div className="topbar-help-item">
                                <strong>Windows</strong>
                                <span>Use the <strong>Download Windows bundle</strong> button on the Agents page, extract to <code>C:\MissionControlAgent</code>, then run <code>.\\install-agent.ps1 -ServerUrl https://missioncontrol.optichosting.co.za -AgentName THIS_COMPUTER_NAME</code> from an admin PowerShell. Confirm with <code>Get-Service MissionControlAgent</code>.</span>
                            </div>
                            <div className="topbar-help-item">
                                <strong>Linux</strong>
                                <span>Use the <strong>Download Linux bundle</strong> button, extract to <code>/opt/mission-control-agent</code>, create <code>agent/config.yaml</code>, create a venv, run <code>python3 -m agent</code>, then install a systemd service. Verify with <code>journalctl -u mission-control-agent</code>.</span>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </header>
    );
}
