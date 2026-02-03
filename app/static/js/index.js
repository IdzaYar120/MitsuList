const nextBtn = document.getElementById("next-airing");
const previousBtn = document.getElementById("previous-airing");
const airingNowDiv = document.getElementById("airing-now-container");

nextBtn.addEventListener("click", function () {
    airingNowDiv.scrollLeft += 400;
});

previousBtn.addEventListener("click", function () {
    airingNowDiv.scrollLeft -= 400;
});

const popNextBtn = document.getElementById("next-popular-anime");
const popPreviousBtn = document.getElementById("previous-popular-anime");
const popDiv = document.getElementById("popular-anime-container");

popNextBtn.addEventListener("click", function () {
    popDiv.scrollLeft += 400;
});

popPreviousBtn.addEventListener("click", function () {
    popDiv.scrollLeft -= 400;
});

const topNextBtn = document.getElementById("next-top-anime");
const topPreviousBtn = document.getElementById("previous-top-anime");
const topDiv = document.getElementById("top-anime-container");

topNextBtn.addEventListener("click", function () {
    topDiv.scrollLeft += 400;
});

topPreviousBtn.addEventListener("click", function () {
    topDiv.scrollLeft -= 400;
});

const movieNextBtn = document.getElementById("next-anime-movie");
const moviePreviousBtn = document.getElementById("previous-anime-movie");
const movieDiv = document.getElementById("anime-movie-container");

movieNextBtn.addEventListener("click", function () {
    movieDiv.scrollLeft += 400;
});

moviePreviousBtn.addEventListener("click", function () {
    movieDiv.scrollLeft -= 400;
});

document.body.addEventListener("click", function (event) {
    if (!event.target.closest("#search-button")) {
        container.innerHTML = "";
        container.style.display = "none";
    }
});

const searchBtn = document.getElementById("search-button");
const container = document.getElementById("container");
const inputBox = document.getElementById("input-box");

function animeContainer(anime) {
    const link = document.createElement("a");
    link.href = `anime/id=${anime.mal_id}`;
    link.classList.add("anime-card-links");

    // Create Card div matching main page style
    const animeCard = document.createElement("div");
    animeCard.classList.add("anime-cards");

    const image = document.createElement("img");
    image.classList.add("image");

    if (anime.images && anime.images.jpg) {
        image.src = anime.images.jpg.large_image_url || anime.images.jpg.image_url;
    }

    const title = document.createElement("p");
    title.classList.add("anime-title");
    title.innerText = anime.title;

    // Optional: Rating badge
    const table = document.createElement("table");
    table.classList.add("airing-now-details-table");
    const tr = document.createElement("tr");
    const td = document.createElement("td");

    let score = anime.score ? anime.score : "N/A";
    td.innerHTML = `<i class="fa-solid fa-star" style="color: gold"></i>&nbsp;${score}`;

    tr.appendChild(td);
    table.appendChild(tr);

    animeCard.appendChild(image);
    animeCard.appendChild(title);
    animeCard.appendChild(table);

    link.appendChild(animeCard);
    container.appendChild(link);
}

searchBtn.addEventListener("click", () => {
    // Prevent spam
    if (searchBtn.disabled) return;

    // Grid Layout Styles
    container.style.display = "grid";
    container.style.gridTemplateColumns = "repeat(auto-fill, minmax(220px, 1fr))";
    container.style.gap = "30px";
    container.style.padding = "40px";
    container.style.justifyContent = "center";
    container.style.width = "90%";
    container.style.margin = "0 auto";

    if (inputBox.value === "") {
        container.style.display = "none";
        return false;
    }

    container.innerHTML = "<div style='color: white; font-size: 1.5rem; width: 100%; text-align: center;'>Loading...</div>";

    // Disable button to prevent double-submit
    searchBtn.disabled = true;

    fetch(`api-proxy/${inputBox.value}`)
        .then(handleResponse)
        .then(handleData)
        .catch(handleError)
        .finally(() => {
            searchBtn.disabled = false;
        });

    function handleResponse(response) {
        return response.json().then(function (json) {
            return response.ok ? json : Promise.reject(json);
        });
    }

    function handleData(data) {
        container.innerHTML = ""; // Clear loading message

        // Jikan returns { data: [...] }
        if (!data.data || data.data.length === 0) {
            container.innerHTML = "<div style='color: white; font-size: 1.5rem; width: 100%; text-align: center;'>No results found.</div>";
            return;
        }

        for (const anime of data.data) {
            animeContainer(anime);
        }
    }

    function handleError(error) {
        container.innerHTML = `<div style='color: red; font-size: 1.5rem; width: 100%; text-align: center;'>Error: ${error.message || error}</div>`;
        console.error(error);
    }
});

document.addEventListener("keypress", function (event) {
    if (event.key === "Enter") {
        searchBtn.click();
    }
});

/* News Carousel Logic */
document.addEventListener("DOMContentLoaded", function () {
    const slides = document.querySelectorAll(".news-item");
    const totalSlides = slides.length;
    let currentSlide = 0;
    let slideInterval;

    function showSlide(index) {
        if (totalSlides === 0) return;

        // Wrap around logic
        if (index >= totalSlides) {
            currentSlide = 0;
        } else if (index < 0) {
            currentSlide = totalSlides - 1;
        } else {
            currentSlide = index;
        }

        // Hide all, show active
        slides.forEach(slide => slide.classList.remove("active"));
        slides[currentSlide].classList.add("active");
    }

    function nextSlide() {
        showSlide(currentSlide + 1);
        resetTimer();
    }

    function prevSlide() {
        showSlide(currentSlide - 1);
        resetTimer();
    }

    function startTimer() {
        slideInterval = setInterval(() => {
            showSlide(currentSlide + 1);
        }, 10000); // 10 seconds (Slower speed)
    }

    function resetTimer() {
        clearInterval(slideInterval);
        startTimer();
    }

    // Initialize Carousel
    if (totalSlides > 0) {
        showSlide(0);
        startTimer();

        // Controls
        const prevBtn = document.getElementById("banner-prev");
        const nextBtn = document.getElementById("banner-next");
        const banner = document.getElementById("news-banner");

        if (prevBtn) {
            prevBtn.addEventListener("click", prevSlide);
        } else {
            console.error("Prev button not found");
        }

        if (nextBtn) {
            nextBtn.addEventListener("click", nextSlide);
        } else {
            console.error("Next button not found");
        }

        // Pause on hover
        if (banner) {
            banner.addEventListener("mouseenter", () => clearInterval(slideInterval));
            banner.addEventListener("mouseleave", startTimer);
        }
    }
});