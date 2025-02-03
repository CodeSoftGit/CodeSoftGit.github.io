class ParticleSystem {
    constructor() {
        this.canvas = document.createElement("canvas");
        this.canvas.className = "particles";
        document.body.prepend(this.canvas);
        this.context = this.canvas.getContext("2d");
        this.particles = [];
        this.resize();
        this.init();
        window.addEventListener("resize", () => this.resize());
    }

    resize() {
        this.canvas.width = window.innerWidth;
        this.canvas.height = window.innerHeight;
    }

    init() {
        this.particles = Array(100).fill().map(() => ({
            x: Math.random() * this.canvas.width,
            y: Math.random() * this.canvas.height,
            size: 2 * Math.random() + 1,
            speed: 0.5 * Math.random() + 0.2,
            angle: Math.random() * Math.PI * 2
        }));
    }

    animate() {
        this.context.fillStyle = "rgba(126, 200, 227, 0.2)";
        this.context.clearRect(0, 0, this.canvas.width, this.canvas.height);
        this.particles.forEach(particle => {
            particle.x += 0.5 * Math.cos(particle.angle);
            particle.y += particle.speed;
            if (particle.y > this.canvas.height) {
                particle.y = 0;
                particle.x = Math.random() * this.canvas.width;
            }
            this.context.beginPath();
            this.context.arc(particle.x, particle.y, particle.size, 0, 2 * Math.PI);
            this.context.fill();
        });
        requestAnimationFrame(() => this.animate());
    }
}

const observer = new IntersectionObserver(entries => {
    entries.forEach((entry, index) => {
        if (entry.isIntersecting) {
            setTimeout(() => {
                entry.target.style.opacity = 1;
                entry.target.style.transform = "translateY(0)";
            }, 150 * index);
        }
    });
}, {
    threshold: 0.1
});

document.querySelectorAll(".project-card, .profile-section, .skill-item").forEach(element => {
    element.style.opacity = 0;
    element.style.transform = "translateY(20px)";
    element.style.transition = "all 0.6s cubic-bezier(0.22, 1, 0.36, 1)";
    observer.observe(element);
});

document.addEventListener("DOMContentLoaded", () => {
    const timeDisplay = document.getElementById("time");

    function updateTime() {
        timeDisplay.textContent = new Date().toLocaleDateString("en-US", {
            timeZone: "America/New_York",
            hour12: true,
            weekday: "long",
            month: "long",
            day: "numeric",
            hour: "numeric",
            minute: "2-digit",
            second: "2-digit"
        }) + " EST";
    }

    setInterval(updateTime, 1000);
    updateTime();

    new ParticleSystem().animate();
    fetchGitHubStats();
    fetchBeatSaberStats();
});

async function fetchGitHubStats(retries = 3, retryDelay = 1000) {
    const cacheKey = "githubStats";
    const cachedData = localStorage.getItem(cacheKey);

    if (cachedData) {
        const { timestamp, data } = JSON.parse(cachedData);
        if (Date.now() - timestamp < 600000) { // 10 minutes
            document.getElementById("repoCount").textContent = data.public_repos;
            return;
        }
    }

    try {
        const response = await fetch("https://api.github.com/users/CodeSoftGit");
        if (response.status === 403 && retries > 0) {
            const retryAfter = response.headers.get("Retry-After") || retryDelay;
            console.warn(`Rate limited. Retrying after ${retryAfter}ms...`);
            await new Promise(resolve => setTimeout(resolve, retryAfter));
            return fetchGitHubStats(retries - 1, retryDelay * 2);
        }
        if (!response.ok) throw new Error("Network response was not ok");

        const data = await response.json();
        document.getElementById("repoCount").textContent = data.public_repos;
        localStorage.setItem(cacheKey, JSON.stringify({
            timestamp: Date.now(),
            data
        }));
    } catch (error) {
        console.error("Fetch error: ", error);
    }
}

function applyBeatSaberStats(stats) {
    const changes = stats.changes;
    const latestChange = changes[changes.length - 1];
    const country = latestChange.newCountry || latestChange.oldCountry;
    const flagUrl = `https://flagcdn.com/h20/${country.toLowerCase()}.png`;

    document.getElementById("bs-rank").textContent = `#${stats.rank.toLocaleString()}`;
    document.getElementById("bs-country-rank").innerHTML = `
        <img src="${flagUrl}" alt="${country} flag" style="margin-right:6px;">
        #${stats.countryRank.toLocaleString()}
    `;
    document.getElementById("bs-pp").textContent = Math.round(stats.pp).toLocaleString();
    document.getElementById("bs-playcount").textContent = stats.scoreStats.totalPlayCount.toLocaleString();

    const clansContainer = document.getElementById("clans-container");
    clansContainer.innerHTML = "";
    stats.clans.forEach(clan => {
        const clanTag = document.createElement("div");
        clanTag.className = "clan-tag";
        clanTag.textContent = clan.tag;
        clanTag.style.color = clan.color;
        clansContainer.appendChild(clanTag);
    });
}

async function fetchBeatSaberStats() {
    const cacheKey = "beatSaberStats";
    const cachedData = localStorage.getItem(cacheKey);

    if (cachedData) {
        const { timestamp, data } = JSON.parse(cachedData);
        if (Date.now() - timestamp < 600000) { // 10 minutes
            applyBeatSaberStats(data);
            return;
        }
    }

    try {
        const response = await fetch("https://api.beatleader.xyz/player/76561199095361711");
        if (!response.ok) throw new Error("Network response was not ok");

        const data = await response.json();
        if (!data || !data.changes || !data.rank || !data.countryRank || !data.pp || !data.scoreStats || !data.clans) {
            throw new Error("Incomplete data");
        }

        localStorage.setItem(cacheKey, JSON.stringify({
            timestamp: Date.now(),
            data
        }));
        applyBeatSaberStats(data);
    } catch (error) {
        console.error("Error fetching Beat Saber stats:", error);
        document.querySelector(".beat-saber-card").style.display = "none";
    }
}

const video = document.getElementById("bs-video");

function loadHighResVideo() {
    const source = video.querySelector("source");
    if (source.dataset.src) {
        source.src = source.dataset.src;
        video.load();
        delete source.dataset.src;
    }
}

const videoObserver = new IntersectionObserver(entries => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            loadHighResVideo();
            video.play();
            animationFrame = requestAnimationFrame(updateGlow);
        } else {
            video.pause();
            cancelAnimationFrame(animationFrame);
        }
    });
});

videoObserver.observe(video);

const canvas = document.createElement("canvas");
const context = canvas.getContext("2d");
let animationFrame;

video.addEventListener("loadeddata", () => {
    canvas.width = 32;
    canvas.height = 32;
});

let lastUpdate = 0;

function updateGlow() {
    if (video.paused || video.ended) return;

    context.drawImage(video, 0, 0, 32, 32);
    const imageData = context.getImageData(12, 12, 8, 8).data;
    let red = 0, green = 0, blue = 0;

    for (let i = 0; i < imageData.length; i += 4) {
        red += imageData[i];
        green += imageData[i + 1];
        blue += imageData[i + 2];
    }

    const pixelCount = imageData.length / 4;
    const glowColor = `rgb(${Math.min(255, Math.round(red / pixelCount * 1.5))}, ${Math.min(255, Math.round(green / pixelCount * 1.5))}, ${Math.min(255, Math.round(blue / pixelCount * 1.5))})`;

    if (Date.now() - lastUpdate > 100) {
        document.querySelector(".beat-saber-card").style.setProperty("--glow-color", glowColor);
        lastUpdate = Date.now();
    }

    animationFrame = requestAnimationFrame(updateGlow);
}

document.addEventListener("DOMContentLoaded", () => {
    new ParticleSystem().animate();
    fetchGitHubStats();
    fetchBeatSaberStats();
});
