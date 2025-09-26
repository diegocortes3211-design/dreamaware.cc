import React from "react";
import FlowApp from "./FlowApp";
import { SettingsProvider } from "./state";

export default function App() {
  return (
    <SettingsProvider>
      <FlowApp />
    </SettingsProvider>
  );
}
