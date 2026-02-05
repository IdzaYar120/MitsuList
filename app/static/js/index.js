/* Fluid Scroll System */
function setupFluidScroll(containerId, nextBtnId, prevBtnId) {
    const container = document.getElementById(containerId);
    const nextBtn = document.getElementById(nextBtnId);
    const prevBtn = document.getElementById(prevBtnId);

    if (!container || !nextBtn || !prevBtn) return;

    // 1. Button Scroll (Page by Page)
    const scrollAmount = () => container.clientWidth * 0.8; // Scroll 80% of width for better context

    nextBtn.addEventListener("click", () => {
        container.scrollBy({ left: scrollAmount(), behavior: 'smooth' });
    });

    prevBtn.addEventListener("click", () => {
        container.scrollBy({ left: -scrollAmount(), behavior: 'smooth' });
    });

    // 2. Drag-to-Scroll Logic
    let isDown = false;
    let startX;
    let scrollLeft;

    container.addEventListener('mousedown', (e) => {
        isDown = true;
        container.classList.add('active'); // CSS class for cursor change
        startX = e.pageX - container.offsetLeft;
        scrollLeft = container.scrollLeft;
    });

    container.addEventListener('mouseleave', () => {
        isDown = false;
        container.classList.remove('active');
    });

    container.addEventListener('mouseup', () => {
        isDown = false;
        container.classList.remove('active');
    });

    container.addEventListener('mousemove', (e) => {
        if (!isDown) return;
        e.preventDefault();
        const x = e.pageX - container.offsetLeft;
        const walk = (x - startX) * 2; // Scroll speed multiplier
        container.scrollLeft = scrollLeft - walk;
    });
}

// Initialize for all containers
document.addEventListener("DOMContentLoaded", () => {
    setupFluidScroll("airing-now-container", "next-airing", "previous-airing");
    setupFluidScroll("popular-anime-container", "next-popular-anime", "previous-popular-anime");
    setupFluidScroll("top-anime-container", "next-top-anime", "previous-top-anime");
    setupFluidScroll("anime-movie-container", "next-anime-movie", "previous-anime-movie");
    setupFluidScroll("recommendations-container", "next-recommendations", "previous-recommendations");
});

// Search & Filter Logic
document.addEventListener("DOMContentLoaded", () => {
    const searchBtn = document.getElementById("search-button");
    const container = document.getElementById("container");
    const resultsWrapper = document.getElementById("search-results-container");
    const closeSearch = document.getElementById("close-search");
    const inputBox = document.getElementById("input-box");
    const toggleFilters = document.getElementById("toggle-filters");
    const filtersPanel = document.getElementById("advanced-filters-panel");
    const genreSelect = document.getElementById("filter-genre");
    const yearInput = document.getElementById("filter-year");
    const typeSelect = document.getElementById("filter-type");
    const applyBtn = document.getElementById("apply-filters");
    const clearBtn = document.getElementById("clear-filters");
    const saveSearchBtn = document.getElementById("save-current-search");
    const savedList = document.getElementById("saved-searches-list");

    // Helper: Build Search Params
    const getSearchParams = () => ({
        q: inputBox.value,
        genres: genreSelect.value,
        year: yearInput.value,
        type: typeSelect.value
    });

    // 1. Toggle Filters
    if (toggleFilters) {
        toggleFilters.addEventListener("click", () => {
            filtersPanel.style.display = filtersPanel.style.display === "none" ? "block" : "none";
        });
    }

    // 2. Fetch Genres
    fetch('/api/genres/')
        .then(res => res.json())
        .then(json => {
            if (json.data) {
                json.data.forEach(genre => {
                    const opt = document.createElement("option");
                    opt.value = genre.mal_id;
                    opt.innerText = genre.name;
                    genreSelect.appendChild(opt);
                });
            }
        });

    // 3. Perform Search
    const performSearch = () => {
        const params = getSearchParams();
        if (!params.q && !params.genres && !params.year && !params.type) return;

        resultsWrapper.style.display = "block";
        container.innerHTML = "<div style='color: white; grid-column: 1/-1; text-align: center;'>Searching...</div>";
        window.scrollTo({ top: resultsWrapper.offsetTop - 100, behavior: 'smooth' });

        const queryStr = new URLSearchParams({
            genres: params.genres,
            year: params.year,
            type: params.type
        }).toString();

        fetch(`/api-proxy/?q=${params.q}&${queryStr}`)
            .then(res => res.json())
            .then(data => {
                container.innerHTML = "";
                if (!data.data || data.data.length === 0) {
                    container.innerHTML = "<div style='color: white; grid-column: 1/-1; text-align: center;'>Nothing found.</div>";
                    return;
                }
                data.data.forEach(anime => animeContainer(anime));
            });
    };

    searchBtn.addEventListener("click", performSearch);
    applyBtn.addEventListener("click", performSearch);

    if (closeSearch) {
        closeSearch.addEventListener("click", () => {
            resultsWrapper.style.display = "none";
        });
    }

    clearBtn.addEventListener("click", () => {
        genreSelect.value = "";
        yearInput.value = "";
        typeSelect.value = "";
    });

    // 4. Saved Searches
    const loadSaved = () => {
        if (!savedList) return;
        fetch('/users/api/saved-searches/')
            .then(res => res.json())
            .then(json => {
                if (json.data && json.data.length > 0) {
                    savedList.innerHTML = "";
                    json.data.slice(0, 5).forEach(s => {
                        const tag = document.createElement("span");
                        tag.className = "saved-search-tag";
                        tag.innerText = s.name;
                        tag.addEventListener("click", () => {
                            inputBox.value = s.params.q || "";
                            genreSelect.value = s.params.genres || "";
                            yearInput.value = s.params.year || "";
                            typeSelect.value = s.params.type || "";
                            performSearch();
                        });
                        savedList.appendChild(tag);
                    });
                }
            });
    };

    if (saveSearchBtn) {
        saveSearchBtn.addEventListener("click", () => {
            const name = prompt("Name your search:");
            if (!name) return;
            fetch('/users/api/save-search/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({ name, params: getSearchParams() })
            }).then(() => loadSaved());
        });
    }

    loadSaved();

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    function animeContainer(anime) {
        const link = document.createElement("a");
        link.href = `anime/id=${anime.mal_id}`;
        link.classList.add("anime-card-links");

        const card = `
            <div class="anime-cards">
                <img src="${anime.images.jpg.large_image_url}" class="image" loading="lazy">
                <p class="anime-title">${anime.title}</p>
                <div class="airing-now-details-table">
                    <i class="fa-solid fa-star" style="color: gold"></i>&nbsp;${anime.score || 'N/A'}
                </div>
            </div>
        `;
        link.innerHTML = card;
        container.appendChild(link);
    }
});

/* Original Carousel & Other Logic Below */
const nextBtn = document.getElementById("next-airing");
// ... (Fluid Scroll initializing is already in setupFluidScroll from previous step)
// Re-adding news logic specifically since it was at the end
document.addEventListener("DOMContentLoaded", () => {
    const slides = document.querySelectorAll(".news-item");
    if (slides.length > 0) {
        let currentSlide = 0;
        const showSlide = (i) => {
            slides.forEach(s => s.classList.remove('active'));
            slides[i].classList.add('active');
        };
        setInterval(() => {
            currentSlide = (currentSlide + 1) % slides.length;
            showSlide(currentSlide);
        }, 10000);
    }
});