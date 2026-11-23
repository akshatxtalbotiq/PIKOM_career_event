"use client";

import { useEffect } from "react";

export default function MotionSystem() {
  useEffect(() => {
    // Check user preference for reduced motion
    const mediaQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
    if (mediaQuery.matches) {
      return;
    }

    const docEl = document.documentElement;
    docEl.classList.add("motion-ready");

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-revealed");
            observer.unobserve(entry.target);
          }
        });
      },
      {
        threshold: 0.05,
        rootMargin: "0px 0px -20px 0px",
      }
    );

    const observeTargets = (root = document) => {
      const targets = root.querySelectorAll(
        "[data-reveal], [data-stagger], .reveal-on-scroll"
      );
      targets.forEach((el) => {
        if (!el.classList.contains("is-revealed")) {
          observer.observe(el);
        }
      });
    };

    observeTargets();

    // Handle dynamically rendered elements from client-side data fetches
    const mutationObserver = new MutationObserver((mutations) => {
      for (const mutation of mutations) {
        if (mutation.addedNodes.length > 0) {
          observeTargets();
          break;
        }
      }
    });

    mutationObserver.observe(document.body, { childList: true, subtree: true });

    return () => {
      observer.disconnect();
      mutationObserver.disconnect();
    };
  }, []);

  return null;
}
