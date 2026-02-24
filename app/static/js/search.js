document.addEventListener("DOMContentLoaded", () => {
    const searchBtn = document.getElementById("search-button");
    const container = document.getElementById("container");
    const inputBox = document.getElementById("input-box");
    const closeSearch = document.getElementById("close-search"); // Might only exist on index

    // Optional filters (only exist on homepage)
    const genreSelect = document.getElementById("filter-genre");
    const yearInput = document.getElementById("filter-year");
    const typeSelect = document.getElementById("filter-type");
    const applyBtn = document.getElementById("apply-filters");
    const resultsWrapper = document.getElementById("search-results-container"); // Wrapper on homepage

    // Helper: Build Search Params
    const getSearchParams = () => {
        const params = {
            q: inputBox ? inputBox.value : ''
        };
        if (genreSelect) params.genres = genreSelect.value;
        if (yearInput) params.year = yearInput.value;
        if (typeSelect) params.type = typeSelect.value;
        return params;
    };

    // Helper: Render Result Card
    function renderAnimeCard(anime) {
        const link = document.createElement("a");
        link.href = `/anime/${anime.mal_id}/`; // Absolute path fix
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

    // Perform Search
    const performSearch = () => {
        const params = getSearchParams();
        if (!params.q && !params.genres && !params.year && !params.type) return;

        // Show loading state
        if (container) {
            container.innerHTML = "<div style='color: white; grid-column: 1/-1; text-align: center; padding: 20px;'>Searching...</div>";
            container.style.display = "grid";
            // Apply grid styles dynamically if not in CSS for #container
            container.style.gridTemplateColumns = "repeat(auto-fill, minmax(200px, 1fr))";
            container.style.gap = "20px";
            container.style.padding = "20px";

            // If we are not on the homepage, resultsWrapper might not exist.
            // In that case, we just show the results in the #container directly under the navbar.
            if (!resultsWrapper) {
                container.style.position = 'absolute';
                container.style.top = '70px';
                container.style.left = '5%';
                container.style.right = '5%';
                container.style.background = 'var(--glass-bg)';
                container.style.backdropFilter = 'blur(15px)';
                container.style.borderRadius = 'var(--border-radius)';
                container.style.zIndex = '1000';
                container.style.boxShadow = '0 10px 40px rgba(0,0,0,0.5)';
                container.style.maxHeight = '80vh';
                container.style.overflowY = 'auto';
            }
        }

        if (resultsWrapper) {
            resultsWrapper.style.display = "block";
            window.scrollTo({ top: resultsWrapper.offsetTop - 100, behavior: 'smooth' });
        }

        const queryParams = new URLSearchParams();
        if (params.q) queryParams.append('q', params.q);
        if (params.genres) queryParams.append('genres', params.genres);
        if (params.year) queryParams.append('year', params.year);
        if (params.type) queryParams.append('type', params.type);

        fetch(`/api/search/?${queryParams.toString()}`)
            .then(res => res.json())
            .then(data => {
                if (container) {
                    container.innerHTML = "";
                    if (!data.data || data.data.length === 0) {
                        container.innerHTML = "<div style='color: white; grid-column: 1/-1; text-align: center;'>Nothing found.</div>";
                        return;
                    }
                    data.data.forEach(anime => renderAnimeCard(anime));
                }
            })
            .catch(err => {
                console.error("Search failed:", err);
                if (container) container.innerHTML = "<div style='color: white; grid-column: 1/-1; text-align: center;'>Error occurred.</div>";
            });
    };

    if (searchBtn) {
        searchBtn.addEventListener("click", performSearch);
    }

    if (applyBtn) {
        applyBtn.addEventListener("click", performSearch);
    }

    // Enter key support
    if (inputBox) {
        inputBox.addEventListener("keypress", function (event) {
            if (event.key === "Enter") {
                performSearch();
            }
        });
    }

    // Close logic
    if (closeSearch && resultsWrapper) {
        closeSearch.addEventListener("click", () => {
            resultsWrapper.style.display = "none";
        });
    }

    // Global close for the navbar search dropdown
    document.addEventListener("click", (e) => {
        if (container && !container.contains(e.target) && inputBox && !inputBox.contains(e.target) && searchBtn && !searchBtn.contains(e.target)) {
            container.style.display = "none";
        }
    });
});
