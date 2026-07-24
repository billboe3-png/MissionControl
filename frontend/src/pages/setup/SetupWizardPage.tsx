import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { setupApi, BootstrapInput } from "../../services/setup";

const TIMEZONE_OPTIONS = [
    "UTC",
    "Africa/Johannesburg",
    "America/New_York",
    "America/Chicago",
    "America/Denver",
    "America/Los_Angeles",
    "Europe/London",
    "Europe/Berlin",
    "Europe/Paris",
    "Asia/Tokyo",
    "Asia/Shanghai",
    "Asia/Kolkata",
    "Australia/Sydney",
    "Pacific/Auckland",
];

const TOTAL_STEPS = 4;

export default function SetupWizardPage() {
    const navigate = useNavigate();
    const [step, setStep] = useState(0);
    const [loading, setLoading] = useState(false);
    const [checking, setChecking] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [data, setData] = useState<BootstrapInput>({
        company_name: "",
        company_code: "",
        site_name: "",
        site_timezone: "UTC",
        admin_display_name: "",
        admin_email: "",
        admin_password: "",
        admin_confirm_password: "",
    });

    const update = (fields: Partial<BootstrapInput>) =>
        setData((prev) => ({ ...prev, ...fields }));

    useEffect(() => {
        setupApi
            .getStatus()
            .then((s) => {
                if (!s.setup_required) navigate("/login", { replace: true });
                else setChecking(false);
            })
            .catch(() => setChecking(false));
    }, [navigate]);

    const validateStep = (): string | null => {
        if (step === 1) {
            if (!data.company_name.trim()) return "Company name is required";
            if (!data.site_name.trim()) return "Site name is required";
        }
        if (step === 2) {
            if (!data.admin_display_name.trim()) return "Display name is required";
            if (!data.admin_email.trim()) return "Email is required";
            if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(data.admin_email))
                return "Invalid email address";
            if (data.admin_password.length < 8)
                return "Password must be at least 8 characters";
            if (data.admin_password !== data.admin_confirm_password)
                return "Passwords do not match";
        }
        return null;
    };

    const next = () => {
        const err = validateStep();
        if (err) {
            setError(err);
            return;
        }
        setError(null);
        if (step < TOTAL_STEPS) setStep(step + 1);
    };

    const prev = () => {
        setError(null);
        if (step > 0) setStep(step - 1);
    };

    const finish = async () => {
        setError(null);
        setLoading(true);
        try {
            await setupApi.bootstrap(data);
            setStep(TOTAL_STEPS + 1);
        } catch (e: any) {
            setError(e.message || "Setup failed");
        } finally {
            setLoading(false);
        }
    };

    const goToLogin = () => navigate("/login");

    if (checking) return <div className="loading-bar" />;

    return (
        <div className="login-container">
            <div className="login-card" style={{ maxWidth: 560 }}>
                {/* Progress bar */}
                {step <= TOTAL_STEPS && (
                    <div style={{ marginBottom: "1.5rem" }}>
                        <div style={{ display: "flex", gap: "0.25rem", marginBottom: "0.5rem" }}>
                            {Array.from({ length: TOTAL_STEPS }, (_, i) => (
                                <div
                                    key={i}
                                    style={{
                                        flex: 1,
                                        height: 3,
                                        borderRadius: 2,
                                        backgroundColor: i <= step ? "#3b82f6" : "#334155",
                                        transition: "background-color 0.3s",
                                    }}
                                />
                            ))}
                        </div>
                        <div style={{ fontSize: "0.75rem", color: "#64748b" }}>
                            Step {Math.min(step + 1, TOTAL_STEPS)} of {TOTAL_STEPS}
                        </div>
                    </div>
                )}

                {error && (
                    <div className="alert alert-error" style={{ marginBottom: "1rem" }}>
                        {error}
                    </div>
                )}

                {/* Step 0: Welcome */}
                {step === 0 && (
                    <>
                        <div className="login-header">
                            <div style={{ fontSize: "3rem", marginBottom: "0.5rem" }}>🚀</div>
                            <h1 style={{ fontSize: "1.5rem" }}>Welcome to Mission Control</h1>
                            <p style={{ color: "#94a3b8", marginTop: "0.5rem" }}>
                                Let&apos;s get your infrastructure management platform set up.
                            </p>
                        </div>
                        <div style={{ color: "#94a3b8", fontSize: "0.9rem", lineHeight: 1.7, margin: "1.5rem 0" }}>
                            <div style={{ marginBottom: "0.5rem" }}>✓ Create your company</div>
                            <div style={{ marginBottom: "0.5rem" }}>✓ Set up your primary site</div>
                            <div style={{ marginBottom: "0.5rem" }}>✓ Create the administrator account</div>
                            <div>✓ Start managing your infrastructure</div>
                        </div>
                        <button
                            className="btn btn-primary btn-block"
                            onClick={next}
                            style={{ marginTop: "1rem" }}
                        >
                            Get Started
                        </button>
                    </>
                )}

                {/* Step 1: Company + Site */}
                {step === 1 && (
                    <>
                        <div className="login-header">
                            <h1 style={{ fontSize: "1.3rem" }}>Company &amp; Site</h1>
                            <p style={{ color: "#94a3b8", marginTop: "0.25rem" }}>
                                Tell us about your organization.
                            </p>
                        </div>
                        <div style={{ marginTop: "1.5rem" }}>
                            <div className="form-group">
                                <label>Company Name *</label>
                                <input
                                    type="text"
                                    value={data.company_name}
                                    onChange={(e) => update({ company_name: e.target.value })}
                                    placeholder="Acme Corp"
                                    autoFocus
                                />
                            </div>
                            <div className="form-group">
                                <label>Company Code</label>
                                <input
                                    type="text"
                                    value={data.company_code ?? ""}
                                    onChange={(e) => update({ company_code: e.target.value })}
                                    placeholder="ACME (optional)"
                                />
                            </div>
                            <div className="form-group">
                                <label>Primary Site Name *</label>
                                <input
                                    type="text"
                                    value={data.site_name}
                                    onChange={(e) => update({ site_name: e.target.value })}
                                    placeholder="Headquarters"
                                />
                            </div>
                            <div className="form-group">
                                <label>Time Zone</label>
                                <select
                                    value={data.site_timezone ?? "UTC"}
                                    onChange={(e) => update({ site_timezone: e.target.value })}
                                >
                                    {TIMEZONE_OPTIONS.map((tz) => (
                                        <option key={tz} value={tz}>{tz}</option>
                                    ))}
                                </select>
                            </div>
                        </div>
                        <div style={{ display: "flex", gap: "0.75rem", marginTop: "1.5rem" }}>
                            <button className="btn btn-secondary" onClick={prev} style={{ flex: 1 }}>
                                Back
                            </button>
                            <button className="btn btn-primary" onClick={next} style={{ flex: 2 }}>
                                Continue
                            </button>
                        </div>
                    </>
                )}

                {/* Step 2: Admin Account */}
                {step === 2 && (
                    <>
                        <div className="login-header">
                            <h1 style={{ fontSize: "1.3rem" }}>Administrator Account</h1>
                            <p style={{ color: "#94a3b8", marginTop: "0.25rem" }}>
                                Create the global administrator account.
                            </p>
                        </div>
                        <div style={{ marginTop: "1.5rem" }}>
                            <div className="form-group">
                                <label>Display Name *</label>
                                <input
                                    type="text"
                                    value={data.admin_display_name}
                                    onChange={(e) => update({ admin_display_name: e.target.value })}
                                    placeholder="John Smith"
                                    autoFocus
                                />
                            </div>
                            <div className="form-group">
                                <label>Email *</label>
                                <input
                                    type="email"
                                    value={data.admin_email}
                                    onChange={(e) => update({ admin_email: e.target.value })}
                                    placeholder="admin@example.com"
                                />
                            </div>
                            <div className="form-group">
                                <label>Password *</label>
                                <input
                                    type="password"
                                    value={data.admin_password}
                                    onChange={(e) => update({ admin_password: e.target.value })}
                                    placeholder="Minimum 8 characters"
                                />
                            </div>
                            <div className="form-group">
                                <label>Confirm Password *</label>
                                <input
                                    type="password"
                                    value={data.admin_confirm_password}
                                    onChange={(e) => update({ admin_confirm_password: e.target.value })}
                                    placeholder="Re-enter password"
                                />
                            </div>
                        </div>
                        <div style={{ display: "flex", gap: "0.75rem", marginTop: "1.5rem" }}>
                            <button className="btn btn-secondary" onClick={prev} style={{ flex: 1 }}>
                                Back
                            </button>
                            <button className="btn btn-primary" onClick={next} style={{ flex: 2 }}>
                                Continue
                            </button>
                        </div>
                    </>
                )}

                {/* Step 3: Review */}
                {step === 3 && (
                    <>
                        <div className="login-header">
                            <h1 style={{ fontSize: "1.3rem" }}>Review &amp; Install</h1>
                            <p style={{ color: "#94a3b8", marginTop: "0.25rem" }}>
                                Confirm your settings before installation.
                            </p>
                        </div>
                        <div style={{ marginTop: "1.5rem", fontSize: "0.9rem" }}>
                            <table style={{ width: "100%", borderCollapse: "collapse" }}>
                                <tbody>
                                    <tr>
                                        <td style={{ padding: "0.5rem 0", color: "#94a3b8", width: "40%" }}>Company</td>
                                        <td style={{ padding: "0.5rem 0", color: "#e2e8f0" }}>{data.company_name}</td>
                                    </tr>
                                    {data.company_code && (
                                        <tr>
                                            <td style={{ padding: "0.5rem 0", color: "#94a3b8" }}>Code</td>
                                            <td style={{ padding: "0.5rem 0", color: "#e2e8f0" }}>{data.company_code}</td>
                                        </tr>
                                    )}
                                    <tr>
                                        <td style={{ padding: "0.5rem 0", color: "#94a3b8" }}>Primary Site</td>
                                        <td style={{ padding: "0.5rem 0", color: "#e2e8f0" }}>{data.site_name}</td>
                                    </tr>
                                    <tr>
                                        <td style={{ padding: "0.5rem 0", color: "#94a3b8" }}>Time Zone</td>
                                        <td style={{ padding: "0.5rem 0", color: "#e2e8f0" }}>{data.site_timezone}</td>
                                    </tr>
                                    <tr>
                                        <td style={{ padding: "0.5rem 0", color: "#94a3b8" }}>Administrator</td>
                                        <td style={{ padding: "0.5rem 0", color: "#e2e8f0" }}>{data.admin_display_name}</td>
                                    </tr>
                                    <tr>
                                        <td style={{ padding: "0.5rem 0", color: "#94a3b8" }}>Email</td>
                                        <td style={{ padding: "0.5rem 0", color: "#e2e8f0" }}>{data.admin_email}</td>
                                    </tr>
                                    <tr>
                                        <td style={{ padding: "0.5rem 0", color: "#94a3b8" }}>Role</td>
                                        <td style={{ padding: "0.5rem 0", color: "#e2e8f0" }}>Global Administrator</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                        <div style={{ display: "flex", gap: "0.75rem", marginTop: "1.5rem" }}>
                            <button className="btn btn-secondary" onClick={prev} style={{ flex: 1 }} disabled={loading}>
                                Back
                            </button>
                            <button className="btn btn-primary" onClick={finish} style={{ flex: 2 }} disabled={loading}>
                                {loading ? "Installing..." : "Install"}
                            </button>
                        </div>
                    </>
                )}

                {/* Step 4: Success */}
                {step === TOTAL_STEPS + 1 && (
                    <>
                        <div className="login-header">
                            <div style={{ fontSize: "3rem", marginBottom: "0.5rem" }}>✅</div>
                            <h1 style={{ fontSize: "1.3rem" }}>Installation Complete</h1>
                            <p style={{ color: "#94a3b8", marginTop: "0.5rem" }}>
                                Mission Control is ready to use.
                            </p>
                        </div>
                        <div style={{ color: "#94a3b8", fontSize: "0.9rem", lineHeight: 1.7, margin: "1.5rem 0" }}>
                            <div style={{ marginBottom: "0.5rem" }}>
                                ✓ Company <strong style={{ color: "#e2e8f0" }}>{data.company_name}</strong> created
                            </div>
                            <div style={{ marginBottom: "0.5rem" }}>
                                ✓ Site <strong style={{ color: "#e2e8f0" }}>{data.site_name}</strong> created
                            </div>
                            <div>
                                ✓ Administrator account <strong style={{ color: "#e2e8f0" }}>{data.admin_email}</strong> created
                            </div>
                        </div>
                        <button
                            className="btn btn-primary btn-block"
                            onClick={goToLogin}
                            style={{ marginTop: "1.5rem" }}
                        >
                            Go to Login
                        </button>
                    </>
                )}
            </div>
        </div>
    );
}
