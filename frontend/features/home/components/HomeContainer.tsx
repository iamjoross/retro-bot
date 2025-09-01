import { useRouter } from "next/router";
import { useState, useEffect } from "react";
import TerminalCard from "../../../widgets/TerminalCard";

export const HomeContainer = () => {
  const router = useRouter();
  const [blinkCursor, setBlinkCursor] = useState(true);

  useEffect(() => {
    const interval = setInterval(() => {
      setBlinkCursor((prev) => !prev);
    }, 500);
    return () => clearInterval(interval);
  }, []);

  const handleStartConversation = () => {
    router.push("/conversation");
  };

  return (
    <div className="center-container">
      <div className="max-w-xl w-full space-y-6">
        {/* Terminal Header */}
        <div className="text-center">
          <TerminalCard>
            <h1 className="terminal-heading">DATACOM-7</h1>
            <div className="terminal-text mb-1">
              Mainframe Computer System • Est. 1978
            </div>
            <div className="terminal-text-muted">
              64KB RAM • Magnetic Tape • 8-inch Floppy
            </div>
          </TerminalCard>
        </div>

        {/* Terminal Window */}
        <TerminalCard statusIndicator={true}>
          <div className="space-y-3 text-sm">
            <div className="terminal-text">&gt; Initializing... *beep*</div>

            <div className="my-6 terminal-text leading-relaxed">
              Hello! I'm DATACOM-7, a friendly mainframe computer from 1978. I
              can help with computing, science, and general knowledge up to
              1982. My memory banks are ready to assist you!
            </div>

            <div className="terminal-prompt">
              &gt; Ready for conversation{blinkCursor ? "_" : " "}
            </div>
          </div>

          <div className="mt-6">
            <button
              onClick={handleStartConversation}
              className="w-full btn-terminal"
            >
              Begin Conversation
            </button>
          </div>
        </TerminalCard>
      </div>
    </div>
  );
};
