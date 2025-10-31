
// Safe version to avoid conflicts on pages that also use video_edit.js.
// It skips YouTube modal handling if the page set window.__VIDEO_EDIT_TAKES_YT__ = true.
(function () {
  const takesYT = !!window.__VIDEO_EDIT_TAKES_YT__;
  if (takesYT) {
    // Optional: only non-YouTube utilities can be initialized here.
    // Leave YouTube modal/handlers to video_edit.js
    return;
  }

  // If another page relies on this file for YouTube (legacy), you can replicate minimal safe init here.
  // For the Edit page, this block will be skipped by the flag above.
})();
