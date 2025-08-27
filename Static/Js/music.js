// Enhanced Music.js with YouTube API Integration
document.addEventListener("DOMContentLoaded", () => {
  initializeMusicApp();
});

// Global variables for music player
let player = null;
let isPlayerReady = false;
let currentPlaylist = [];
let currentTrackIndex = 0;
let isPlaying = false;
let isShuffled = false;
let isRepeating = false;
let currentVolume = 70;

// YouTube API ready callback
window.onYouTubeIframeAPIReady = function() {
  console.log('YouTube API Ready');
  isPlayerReady = true;
};

function initializeMusicApp() {
  // Fetch daily quote
  fetchDailyQuote();
  
  // Initialize player controls
  setupPlayerControls();
  
  // Setup mood card interactions
  setupMoodInteractions();
  
  // Setup playlist interactions
  setupPlaylistInteractions();
  
  // Load user session data
  loadUserSession();
}

function fetchDailyQuote() {
  const quoteEl = document.getElementById("daily-quote");
  
  fetch("https://api.quotable.io/random?tags=motivational|inspirational")
    .then(res => res.json())
    .then(data => {
      quoteEl.textContent = `"${data.content}" — ${data.author}`;
    })
    .catch(() => {
      const quotes = [
        "Music can heal the wounds that words cannot touch.",
        "Where words fail, music speaks.",
        "Music is the universal language of mankind.",
        "Life is a song - sing it with passion.",
        "Music is therapy for the soul."
      ];
      const randomQuote = quotes[Math.floor(Math.random() * quotes.length)];
      quoteEl.textContent = randomQuote;
    });
}

function setupPlayerControls() {
  const playBtn = document.getElementById('playBtn');
  const prevBtn = document.getElementById('prevBtn');
  const nextBtn = document.getElementById('nextBtn');
  const shuffleBtn = document.getElementById('shuffleBtn');
  const repeatBtn = document.getElementById('repeatBtn');
  const volumeSlider = document.getElementById('volumeSlider');
  const progressBar = document.getElementById('progressBar');

  if (playBtn) {
    playBtn.addEventListener('click', togglePlayPause);
  }
  
  if (prevBtn) {
    prevBtn.addEventListener('click', playPrevious);
  }
  
  if (nextBtn) {
    nextBtn.addEventListener('click', playNext);
  }
  
  if (shuffleBtn) {
    shuffleBtn.addEventListener('click', toggleShuffle);
  }
  
  if (repeatBtn) {
    repeatBtn.addEventListener('click', toggleRepeat);
  }
  
  if (volumeSlider) {
    volumeSlider.addEventListener('input', adjustVolume);
  }
  
  if (progressBar) {
    progressBar.addEventListener('click', seekToPosition);
  }
}

function setupMoodInteractions() {
  const moodCards = document.querySelectorAll('.mood-card');
  
  moodCards.forEach(card => {
    card.addEventListener('click', function(e) {
      e.preventDefault();
      const mood = this.dataset.mood;
      loadMoodPlaylist(mood);
      
      // Update active state
      moodCards.forEach(c => c.classList.remove('active'));
      this.classList.add('active');
    });
  });
}

function setupPlaylistInteractions() {
  const playlistBtns = document.querySelectorAll('.playlist-play-btn');
  
  playlistBtns.forEach(btn => {
    btn.addEventListener('click', function(e) {
      e.preventDefault();
      const playlistData = JSON.parse(this.dataset.playlist || '{}');
      loadYouTubePlaylist(playlistData);
    });
  });
}

function loadMoodPlaylist(mood) {
  // Show loading state
  showLoadingState();
  
  // Fetch mood-specific playlists from backend
  fetch(`/api/mood-playlists/${mood}`)
    .then(response => response.json())
    .then(data => {
      displayMoodPlaylists(data);
      hideLoadingState();
    })
    .catch(error => {
      console.error('Error loading mood playlist:', error);
      hideLoadingState();
      showErrorMessage('Failed to load playlist. Please try again.');
    });
}

function loadYouTubePlaylist(playlistData) {
  const musicPlayer = document.getElementById('musicPlayer');
  
  if (!musicPlayer) return;
  
  // Show the player
  musicPlayer.style.display = 'block';
  
  // Update player info
  updatePlayerInfo(playlistData.name, playlistData.description);
  
  // Extract playlist ID from URL
  const playlistId = extractPlaylistId(playlistData.url);
  
  if (playlistId) {
    createYouTubePlayer(playlistId);
  }
  
  // Start music session tracking
  startMusicSession(playlistData);
}

function extractPlaylistId(url) {
  const match = url.match(/[&?]list=([^&]+)/);
  return match ? match[1] : null;
}

function createYouTubePlayer(playlistId) {
  // Remove existing player if any
  if (player) {
    player.destroy();
  }
  
  // Create hidden YouTube player for audio control
  const playerContainer = document.createElement('div');
  playerContainer.id = 'youtube-player';
  playerContainer.style.display = 'none';
  document.body.appendChild(playerContainer);
  
  player = new YT.Player('youtube-player', {
    height: '0',
    width: '0',
    playerVars: {
      listType: 'playlist',
      list: playlistId,
      autoplay: 1,
      controls: 0,
      disablekb: 1,
      enablejsapi: 1,
      modestbranding: 1,
      rel: 0,
      showinfo: 0
    },
    events: {
      onReady: onPlayerReady,
      onStateChange: onPlayerStateChange,
      onError: onPlayerError
    }
  });
}

function onPlayerReady(event) {
  console.log('Player ready');
  player.setVolume(currentVolume);
  updatePlayerUI();
  startProgressUpdater();
}

function onPlayerStateChange(event) {
  const state = event.data;
  
  switch(state) {
    case YT.PlayerState.PLAYING:
      isPlaying = true;
      updatePlayButton();
      break;
    case YT.PlayerState.PAUSED:
      isPlaying = false;
      updatePlayButton();
      break;
    case YT.PlayerState.ENDED:
      playNext();
      break;
  }
}

function onPlayerError(event) {
  console.error('YouTube player error:', event.data);
  showErrorMessage('Playback error occurred. Trying next track...');
  setTimeout(() => playNext(), 2000);
}

function togglePlayPause() {
  if (!player) return;
  const playBtn = document.getElementById('playBtn');
  const icon = playBtn ? playBtn.querySelector('i') : null;
  if (isPlaying) {
    if (icon) icon.className = 'fas fa-play';
    player.pauseVideo();
  } else {
    if (icon) icon.className = 'fas fa-pause';
    player.playVideo();
  }
}

function playNext() {
  if (!player) return;
  player.nextVideo();
}

function playPrevious() {
  if (!player) return;
  player.previousVideo();
}

function toggleShuffle() {
  isShuffled = !isShuffled;
  const shuffleBtn = document.getElementById('shuffleBtn');
  if (shuffleBtn) {
    shuffleBtn.classList.toggle('active', isShuffled);
  }
  
  if (player) {
    player.setShuffle(isShuffled);
  }
}

function toggleRepeat() {
  isRepeating = !isRepeating;
  const repeatBtn = document.getElementById('repeatBtn');
  if (repeatBtn) {
    repeatBtn.classList.toggle('active', isRepeating);
  }
  
  if (player) {
    player.setLoop(isRepeating);
  }
}

function adjustVolume(event) {
  currentVolume = parseInt(event.target.value);
  if (player) {
    player.setVolume(currentVolume);
  }
}

function seekToPosition(event) {
  if (!player) return;
  
  const progressBar = event.currentTarget;
  const rect = progressBar.getBoundingClientRect();
  const clickX = event.clientX - rect.left;
  const percentage = clickX / rect.width;
  
  const duration = player.getDuration();
  const seekTime = duration * percentage;
  
  player.seekTo(seekTime);
}

function updatePlayerInfo(title, description) {
  const songEl = document.getElementById('currentSong');
  const artistEl = document.getElementById('currentArtist');
  
  if (songEl) songEl.textContent = title;
  if (artistEl) artistEl.textContent = description;
}

function updatePlayButton() {
  const playBtn = document.getElementById('playBtn');
  if (playBtn) {
    const icon = playBtn.querySelector('i');
    if (isPlaying) {
      icon.className = 'fas fa-pause';
    } else {
      icon.className = 'fas fa-play';
    }
  }
}

function startProgressUpdater() {
  setInterval(() => {
    if (player && isPlaying) {
      updateProgress();
    }
  }, 1000);
}

function updateProgress() {
  if (!player) return;
  
  const currentTime = player.getCurrentTime();
  const duration = player.getDuration();
  
  if (duration > 0) {
    const percentage = (currentTime / duration) * 100;
    const progressFill = document.getElementById('progressFill');
    if (progressFill) {
      progressFill.style.width = percentage + '%';
    }
    
    // Update time display
    const currentTimeEl = document.getElementById('currentTime');
    const durationEl = document.getElementById('duration');
    
    if (currentTimeEl) {
      currentTimeEl.textContent = formatTime(currentTime);
    }
    if (durationEl) {
      durationEl.textContent = formatTime(duration);
    }
  }
}

function formatTime(seconds) {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}

function startMusicSession(playlistData) {
  const sessionData = {
    mood: getCurrentMood(),
    playlist_name: playlistData.name,
    playlist_url: playlistData.url,
    start_time: new Date().toISOString()
  };
  
  // Send to backend for session tracking
  fetch('/api/music-session/start', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(sessionData)
  });
  
  // Show session timer
  showSessionTimer();
}

function getCurrentMood() {
  const activeMoodCard = document.querySelector('.mood-card.active');
  return activeMoodCard ? activeMoodCard.dataset.mood : 'unknown';
}

function showSessionTimer() {
  const timer = document.getElementById('sessionTimer');
  if (timer) {
    timer.style.display = 'block';
    startSessionTimer();
  }
}

function startSessionTimer() {
  let sessionSeconds = 0;
  const timerDisplay = document.getElementById('sessionTime');
  
  const interval = setInterval(() => {
    sessionSeconds++;
    if (timerDisplay) {
      timerDisplay.textContent = formatTime(sessionSeconds);
    }
    
    if (!isPlaying) {
      clearInterval(interval);
    }
  }, 1000);
}

function showLoadingState() {
  // Add loading spinner or message
  console.log('Loading playlist...');
}

function hideLoadingState() {
  // Remove loading spinner or message
  console.log('Playlist loaded');
}

function showErrorMessage(message) {
  // Show user-friendly error message
  console.error(message);
}

function loadUserSession() {
  // Load any saved user preferences or session data
  const savedVolume = localStorage.getItem('musicVolume');
  if (savedVolume) {
    currentVolume = parseInt(savedVolume);
    const volumeSlider = document.getElementById('volumeSlider');
    if (volumeSlider) {
      volumeSlider.value = currentVolume;
    }
  }
}

function updatePlayerUI() {
  // Update all player UI elements
  updatePlayButton();
}

// Utility functions for playlist management
function displayMoodPlaylists(data) {
  // This would update the playlist display based on mood selection
  console.log('Displaying mood playlists:', data);
}

// Enhanced playlist button functionality
function startMusicSession(mood, playlistName, playlistUrl) {
  const playlistData = {
    name: playlistName,
    url: playlistUrl,
    description: `${mood} mood playlist`
  };
  
  loadYouTubePlaylist(playlistData);
}

// Legacy function support
function playAllTracks() {
  const activePlaylist = document.querySelector('.playlist-item:first-child .playlist-play-btn');
  if (activePlaylist) {
    activePlaylist.click();
  }
}

function shufflePlaylist() {
  toggleShuffle();
}

function downloadPlaylist() {
  showErrorMessage('Download feature coming soon!');
}

function endMusicSession() {
  if (player) {
    player.pauseVideo();
  }
  
  const sessionTimer = document.getElementById('sessionTimer');
  if (sessionTimer) {
    sessionTimer.style.display = 'none';
  }
  
  // Send session end to backend
  fetch('/api/music-session/end', { method: 'POST' });
}

function toggleTrack(index) {
  console.log('Toggle track:', index);
  // This function can be enhanced based on specific track management needs
}