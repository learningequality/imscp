// Add handlers to save and load from localStorage on initialize and finish
// Requires scormAPI.js to be loaded from github.com/gabrieldoty/simplify-scorm
window.API && window.localStorage && (function() {
  var SCORM_KEY = 'scormData';

  if (localStorage[SCORM_KEY]) {
    API.loadFromJSON(JSON.parse(localStorage[SCORM_KEY]));
  }

  API.on("LMSCommit", function() {
    localStorage[SCORM_KEY] = JSON.stringify(API.cmi.toJSON());
  });

  API.on("LMSFinish", function() {
    localStorage[SCORM_KEY] = JSON.stringify(API.cmi.toJSON());
  });
})();
