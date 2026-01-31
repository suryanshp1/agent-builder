/**
 * CopilotKit Provider Setup
 * 
 * Integrates AI-powered copilot for agent configuration assistance
 */

import { CopilotKit } from "@copilotkit/react-core";
import "@copilotkit/react-ui/styles.css";
import { ReactNode } from "react";

interface CopilotProviderProps {
    children: ReactNode;
}

export function CopilotProvider({ children }: CopilotProviderProps) {
    return (
        <CopilotKit
            runtimeUrl="/api/copilot"
        >
            {children}
        </CopilotKit>
    );
}
