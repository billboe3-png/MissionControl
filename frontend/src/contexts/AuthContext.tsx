import { createContext, useContext, useState, useEffect, ReactNode } from "react";
import { authApi, UserInfo, getStoredToken, getStoredUser, storeAuth, clearAuth } from "../services/auth";

interface AuthState {
    token: string | null;
    user: UserInfo | null;
    loading: boolean;
}

interface AuthContextType extends AuthState {
    login: (email: string, password: string) => Promise<void>;
    logout: () => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function useAuth(): AuthContextType {
    const ctx = useContext(AuthContext);
    if (!ctx) throw new Error("useAuth must be used within AuthProvider");
    return ctx;
}

export function AuthProvider({ children }: { children: ReactNode }) {
    const [state, setState] = useState<AuthState>({
        token: getStoredToken(),
        user: getStoredUser(),
        loading: true,
    });

    useEffect(() => {
        const token = getStoredToken();
        const user = getStoredUser();
        setState({ token, user, loading: false });
    }, []);

    const login = async (email: string, password: string) => {
        const result = await authApi.login(email, password);
        storeAuth(result.access_token, result.user);
        setState({ token: result.access_token, user: result.user, loading: false });
    };

    const logout = () => {
        clearAuth();
        setState({ token: null, user: null, loading: false });
    };

    return (
        <AuthContext.Provider value={{ ...state, login, logout }}>
            {children}
        </AuthContext.Provider>
    );
}
