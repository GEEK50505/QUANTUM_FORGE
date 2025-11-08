/**
 * frontend/src/hooks/useGoBack.ts
 *
 * Purpose:
 *  - Simple hook to navigate back in history or fall back to the app root.
 *
 * Exports:
 *  - default export: useGoBack(): () => void
 *
 * Usage:
 *  const goBack = useGoBack();
 *  goBack();
 */

import { useNavigate } from "react-router-dom";

const useGoBack = () => {
  const navigate = useNavigate();

  const goBack = () => {
    if (window.history.state && window.history.state.idx > 0) {
      navigate(-1); // Go back to the previous page
    } else {
      navigate("/"); // Redirect to home if no history exists
    }
  };

  return goBack;
};

export default useGoBack;
