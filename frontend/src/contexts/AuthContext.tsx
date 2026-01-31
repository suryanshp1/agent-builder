/**
 * Authentication Context
 * 
 * Provides global authentication state and methods
 */

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { apiClient, User } from '../lib/api';

interface AuthContextType {
    user: User | null;
    isAuthenticated: boolean;
    isLoading: boolean;
    login: (email: string, password: string) => Promise<void>;
    signup: (email: string, password: string, organizationId: string) => Promise<void>;
    logout: () => void;
    checkAuth: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
    const [user, setUser] = useState<User | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    const checkAuth = async () => {
        try {
            const currentUser = await apiClient.getCurrentUser();
            setUser(currentUser);
        } catch (error) {
            setUser(null);
            apiClient.clearTokens();
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        // Check authentication on mount
        const token = localStorage.getItem('access_token');
        if (token) {
            checkAuth();
        } else {
            setIsLoading(false);
        }
    }, []);

    const login = async (email: string, password: string) => {
        try {
            await apiClient.login(email, password);
            await checkAuth();
        } catch (error) {
            throw error;
        }
    };

    const signup = async (email: string, password: string, organizationId: string) => {
        try {
            await apiClient.signup(email, password, organizationId);
            await checkAuth();
        } catch (error) {
            throw error;
        }
    };

    const logout = () => {
        apiClient.logout();
        setUser(null);
    };

    const value = {
        user,
        isAuthenticated: !!user,
        isLoading,
        login,
        signup,
        logout,
        checkAuth,
    };

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
}
