import { Outlet } from "react-router-dom";
import Sidebar from "./Sidebar";
import TopBar from "./TopBar";
import StatusBar from "./StatusBar";

export default function AppLayout() {
    return (
        <div className="app-layout">
            <Sidebar />
            <div className="app-main">
                <TopBar />
                <main className="app-content">
                    <Outlet />
                </main>
                <StatusBar />
            </div>
        </div>
    );
}
