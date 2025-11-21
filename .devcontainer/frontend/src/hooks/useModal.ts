/**
 * frontend/src/hooks/useModal.ts
 *
 * Purpose:
 *  - Small React hook to manage modal visibility state (open/close/toggle).
 *
 * Exports:
 *  - useModal(initialState?: boolean): { isOpen, openModal, closeModal, toggleModal }
 *
 * Usage:
 *  const { isOpen, openModal, closeModal } = useModal();
 */

import { useState, useCallback } from "react";

export const useModal = (initialState: boolean = false) => {
  const [isOpen, setIsOpen] = useState(initialState);

  const openModal = useCallback(() => setIsOpen(true), []);
  const closeModal = useCallback(() => setIsOpen(false), []);
  const toggleModal = useCallback(() => setIsOpen((prev) => !prev), []);

  return { isOpen, openModal, closeModal, toggleModal };
};
