import { useRef, useCallback, useEffect } from "react";

export const useAutoScroll = <T extends HTMLElement = HTMLDivElement>() => {
  const scrollRef = useRef<T>(null);

  const scrollToBottom = useCallback(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, []);

  return { scrollRef, scrollToBottom };
};

export const useAutoScrollOnChange = <T extends HTMLElement = HTMLDivElement>(
  dependency: unknown
) => {
  const { scrollRef, scrollToBottom } = useAutoScroll<T>();

  useEffect(() => {
    scrollToBottom();
  }, [dependency, scrollToBottom]);

  return { scrollRef, scrollToBottom };
};
