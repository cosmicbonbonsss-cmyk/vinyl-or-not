/**
 * Shared project gallery config (Firebase or local fallback).
 * With the firebase fields empty, projects are saved in this browser only (local fallback).
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
