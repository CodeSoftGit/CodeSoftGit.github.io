class ParticleSystem {
    constructor() {
        this.canvas = document.createElement("canvas"), this.canvas
            .className = "particles", document.body.prepend(this.canvas),
            this.ctx = this.canvas
            .getContext("2d"), this.particles = [], this.resize(), this
            .init(), window.addEventListener("resize", () => this.resize())
    }
    resize() {
        this.canvas.width = window.innerWidth, this.canvas.height = window
            .innerHeight
    }
    init() {
        this.particles = Array(100).fill().map(() => ({
            x: Math.random() * this.canvas.width,
            y: Math.random() * this.canvas.height,
            size: 2 * Math.random() + 1,
            speed: .5 * Math.random() + .2,
            angle: Math.random() * Math.PI * 2
        }))
    }
    animate() {
        this.ctx.fillStyle = "rgba(126, 200, 227, 0.2)", this.ctx.clearRect(
                0, 0, this.canvas.width, this.canvas.height), this.particles
            .forEach(t => {
                t.x += .5 * Math.cos(t.angle), t.y += t.speed, t.y >
                    this.canvas.height && (t.y = 0, t.x = Math
                        .random() * this.canvas.width), this.ctx
                    .beginPath(), this.ctx.arc(t.x, t.y, t.size, 0, 2 *
                        Math.PI), this.ctx.fill()
            }), requestAnimationFrame(() => this.animate())
    }
}
const observer = new IntersectionObserver(t => {
    t.forEach((t, e) => {
        t.isIntersecting && setTimeout(() => {
            t.target.style.opacity = 1, t.target.style
                .transform = "translateY(0)"
        }, 150 * e)
    })
}, {
    threshold: .1
});
document.querySelectorAll(".project-card, .profile-section, .skill-item")
    .forEach(t => {
        t.style.opacity = 0, t.style.transform = "translateY(20px)", t.style
            .transition = "all 0.6s cubic-bezier(0.22, 1, 0.36, 1)",
            observer.observe(t)
    });
const timeDisplay = document.getElementById("time");

function updateTime() {
    timeDisplay.textContent = new Date().toLocaleDateString("en-US", {
        timeZone: "America/New_York",
        hour12: !0,
        weekday: "long",
        month: "long",
        day: "numeric",
        hour: "numeric",
        minute: "2-digit",
        second: "2-digit"
    }) + " EST"
}
async function fetchGitHubStats(t = 3, e = 1e3) {
    let a = "githubStats",
        n = localStorage.getItem(a);
    if (n) {
        let {
            timestamp: s,
            data: i
        } = JSON.parse(n);
        if (Date.now() - s < 6e5) {
            document.getElementById("repoCount").textContent = i
                .public_repos;
            return
        }
    }
    try {
        let r = await fetch("https://api.github.com/users/CodeSoftGit");
        if (403 === r.status && t > 0) {
            let o = r.headers.get("Retry-After") || e;
            return console.warn(`Rate limited. Retrying after ${o}ms...`),
                await new Promise(t => setTimeout(t, o)), fetchGitHubStats(
                    t - 1, 2 * e)
        }
        if (!r.ok) throw Error("Network response was not ok");
        let c = await r.json();
        document.getElementById("repoCount").textContent = c.public_repos,
            localStorage.setItem(a, JSON.stringify({
                timestamp: Date.now(),
                data: c
            }))
    } catch (l) {
        console.error("Fetch error: ", l)
    }
}

function applyBeatSaberStats(t) {
    let e = t.changes,
        a = e[e.length - 1],
        n = a.newCountry || a.oldCountry,
        s = `https://flagcdn.com/h20/${n.toLowerCase()}.png`;
    document.getElementById("bs-rank").textContent =
        `#${t.rank.toLocaleString()}`, document.getElementById(
            "bs-country-rank").innerHTML = `
                            <img src="${s}" alt="${n} flag" style="margin-right:6px;">
                            #${t.countryRank.toLocaleString()}
                        `, document.getElementById("bs-pp").textContent = Math
        .round(t.pp).toLocaleString(), document.getElementById("bs-playcount")
        .textContent = t.scoreStats.totalPlayCount.toLocaleString();
    let i = document.getElementById("clans-container");
    i.innerHTML = "", t.clans.forEach(t => {
        let e = document.createElement("div");
        e.className = "clan-tag", e.textContent = t.tag, e.style.color =
            t.color, i.appendChild(e)
    })
}
async function fetchBeatSaberStats() {
    let t = "beatSaberStats",
        e = localStorage.getItem(t);
    if (e) {
        let {
            timestamp: a,
            data: n
        } = JSON.parse(e);
        if (Date.now() - a < 6e5) {
            applyBeatSaberStats(n);
            return
        }
    }
    try {
        let s = await fetch(
            "https://api.beatleader.xyz/player/76561199095361711");
        if (!s.ok) throw Error("Network response was not ok");
        let i = await s.json();
        if (!i || !i.changes || !i.rank || !i.countryRank || !i.pp || !i
            .scoreStats || !i.clans) throw Error("Incomplete data");
        localStorage.setItem(t, JSON.stringify({
            timestamp: Date.now(),
            data: i
        })), applyBeatSaberStats(i)
    } catch (r) {
        console.error("Error fetching Beat Saber stats:", r), document
            .querySelector(".beat-saber-card").style.display = "none"
    }
}
setInterval(updateTime, 1e3), updateTime();
const video = document.getElementById("bs-video");

function loadHighResVideo() {
    let t = video.querySelector("source");
    t.dataset.src && (t.src = t.dataset.src, video.load(), delete t.dataset.src)
}
const videoObserver = new IntersectionObserver(t => {
    t.forEach(t => {
        t.isIntersecting ? (loadHighResVideo(), video.play(),
            animationFrame = requestAnimationFrame(
                updateGlow)) : (video.pause(),
            cancelAnimationFrame(animationFrame))
    })
});
videoObserver.observe(video);
const canvas = document.createElement("canvas"),
    ctx = canvas.getContext("2d");
let animationFrame;
video.addEventListener("loadeddata", () => {
    canvas.width = 32, canvas.height = 32
});
let lastUpdate = 0;

function updateGlow() {
    if (video.paused || video.ended) return;
    ctx.drawImage(video, 0, 0, 32, 32);
    let t = ctx.getImageData(12, 12, 8, 8).data,
        e = 0,
        a = 0,
        n = 0;
    for (let s = 0; s < t.length; s += 4) e += t[s], a += t[s + 1], n += t[s +
        2];
    let i = t.length / 4,
        r =
        `rgb(${Math.min(255,Math.round(e/i*1.5))}, ${Math.min(255,Math.round(a/i*1.5))}, ${Math.min(255,Math.round(n/i*1.5))})`;
    Date.now() - lastUpdate > 100 && (document.querySelector(".beat-saber-card")
            .style.setProperty("--glow-color", r), lastUpdate = Date.now()),
        animationFrame = requestAnimationFrame(updateGlow)
}
document.addEventListener("DOMContentLoaded", () => {
    new ParticleSystem().animate(), fetchGitHubStats(),
        fetchBeatSaberStats()
});
