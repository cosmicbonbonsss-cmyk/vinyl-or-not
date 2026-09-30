/**
 * Shared project gallery config (Firebase or local fallback).
 * Leave firebase fields empty until backend keys are filled by the parent agent.
 * Do not invent API keys.
 */
window.VON_GALLERY = {
  provider: "firebase", // or "local-fallback"
  firebase: {
    apiKey: "",
    authDomain: "",
    projectId: "",
    storageBucket: "",
    messagingSenderId: "",
    appId: ""
  },
  collection: "projects"
};
