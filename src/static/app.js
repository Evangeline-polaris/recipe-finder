/**
 * Recipe Finder SPA — Frontend Application
 * Handles all pages: Search, Weekly Plan, Rating, Favorites.
 */
(function () {
    'use strict';

    // ─────────────────────────────────────────────
    // Global State
    // ─────────────────────────────────────────────
    const state = {
        ingredients: [],           // current ingredient tags
        filters: null,             // { cuisine_groups, all_cuisines, dietary_tags }
        searchResults: null,       // last search result
        lastSearchParams: null,    // { ingredients, allow_substitution, ... }
        currentPage: 'search',
        // for weekly plan
        planResults: null,
        planUserNormalized: null,
        // for favorites / rate
        allRecipes: [],
    };

    // ─────────────────────────────────────────────
    // DOM References
    // ─────────────────────────────────────────────
    const $ = (sel) => document.querySelector(sel);
    const $$ = (sel) => document.querySelectorAll(sel);

    const appEl = $('#app');
    const loadingEl = $('#loadingOverlay');
    const toastContainer = $('#toastContainer');
    const recipeModal = $('#recipeModal');
    const recipeModalContent = $('#recipeModalContent');

    // Bootstrap modal instance (lazy init)
    let bsModal = null;
    function getBsModal() {
        if (!bsModal) bsModal = new bootstrap.Modal(recipeModal);
        return bsModal;
    }

    // ─────────────────────────────────────────────
    // Utilities
    // ─────────────────────────────────────────────
    function showLoading() { loadingEl.classList.remove('d-none'); }
    function hideLoading() { loadingEl.classList.add('d-none'); }

    function showToast(msg, type = 'success') {
        const id = 'toast-' + Date.now();
        const bgClass = type === 'error' ? 'bg-danger text-white' : 'bg-success text-white';
        const html = `
            <div id="${id}" class="toast align-items-center ${bgClass} border-0" role="alert" aria-live="assertive" aria-atomic="true">
                <div class="d-flex">
                    <div class="toast-body">${msg}</div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
                </div>
            </div>`;
        toastContainer.insertAdjacentHTML('beforeend', html);
        const toastEl = document.getElementById(id);
        const toast = new bootstrap.Toast(toastEl, { delay: 3000 });
        toast.show();
        toastEl.addEventListener('hidden.bs.toast', () => toastEl.remove());
    }

    async function api(url, options = {}) {
        let resp;
        try {
            resp = await fetch(url, {
                headers: { 'Content-Type': 'application/json', ...options.headers },
                ...options,
            });
        } catch (e) {
            throw new Error('无法连接到服务器，请确认已运行 python run_web.py');
        }
        if (!resp.ok) {
            const err = await resp.json().catch(() => ({ detail: '请求失败' }));
            throw new Error(err.detail || `服务器错误 (HTTP ${resp.status})`);
        }
        return resp.json();
    }

    function matchClass(ratio) {
        if (ratio >= 0.7) return 'match-high';
        if (ratio >= 0.4) return 'match-mid';
        return 'match-low';
    }

    function formatPct(ratio) { return Math.round(ratio * 100) + '%'; }

    // ─────────────────────────────────────────────
    // Navigation / Routing
    // ─────────────────────────────────────────────
    function navigate(page) {
        state.currentPage = page;
        // Update nav active
        $$('.nav-link').forEach(el => {
            el.classList.toggle('active', el.dataset.page === page);
        });
        renderPage(page);
    }

    function renderPage(page) {
        switch (page) {
            case 'search': renderSearchPage(); break;
            case 'weekly': renderWeeklyPlanPage(); break;
            case 'rate': renderRatePage(); break;
            case 'favorites': renderFavoritesPage(); break;
            default: renderSearchPage();
        }
    }

    // Attach nav listeners
    document.addEventListener('click', (e) => {
        const navLink = e.target.closest('[data-page]');
        if (navLink) {
            e.preventDefault();
            navigate(navLink.dataset.page);
        }
    });

    // ─────────────────────────────────────────────
    // Ingredient Tag Input (shared component)
    // ─────────────────────────────────────────────
    function createTagInput(container, initialTags = [], placeholder = '输入食材名称，按回车添加...') {
        container.innerHTML = '';
        const area = document.createElement('div');
        area.className = 'ingredient-input-area';
        const input = document.createElement('input');
        input.type = 'text';
        input.placeholder = placeholder;
        area.appendChild(input);
        container.appendChild(area);

        const tags = [...initialTags];

        function renderTags() {
            // Remove all tag elements (keep input)
            area.querySelectorAll('.ingredient-tag').forEach(el => el.remove());
            tags.forEach((tag, idx) => {
                const tagEl = document.createElement('span');
                tagEl.className = 'ingredient-tag';
                tagEl.innerHTML = `${tag}<span class="tag-remove" data-idx="${idx}">&times;</span>`;
                area.insertBefore(tagEl, input);
            });
        }

        function addTag(val) {
            const v = val.trim();
            if (v && !tags.includes(v)) {
                tags.push(v);
                renderTags();
            }
        }

        function removeTag(idx) {
            tags.splice(idx, 1);
            renderTags();
        }

        area.addEventListener('click', (e) => {
            const removeBtn = e.target.closest('.tag-remove');
            if (removeBtn) {
                removeTag(parseInt(removeBtn.dataset.idx));
            } else {
                input.focus();
            }
        });

        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                addTag(input.value);
                input.value = '';
            }
            if (e.key === 'Backspace' && input.value === '' && tags.length > 0) {
                removeTag(tags.length - 1);
            }
        });

        renderTags();

        return {
            getTags: () => [...tags],
            setTags: (newTags) => { tags.length = 0; tags.push(...newTags); renderTags(); },
            clear: () => { tags.length = 0; renderTags(); },
        };
    }

    // ─────────────────────────────────────────────
    // Filters Bar Component
    // ─────────────────────────────────────────────
    function renderFiltersBar(container, onFilterChange) {
        if (!state.filters) return;
        container.innerHTML = '';

        const f = state.filters;

        // Cuisine filter — dropdown group
        const cuisineGroup = document.createElement('div');
        cuisineGroup.className = 'dropdown';
        cuisineGroup.innerHTML = `
            <button class="btn btn-sm btn-outline-secondary dropdown-toggle" type="button" data-bs-toggle="dropdown">
                <i class="bi bi-funnel"></i> 菜系
            </button>
            <div class="dropdown-menu p-3" style="min-width: 280px; max-height: 350px; overflow-y: auto;">
                ${Object.entries(f.cuisine_groups).map(([region, cuisines]) => `
                    <div class="mb-2">
                        <strong class="text-muted small">${region}</strong>
                        <div class="d-flex flex-wrap gap-1 mt-1">
                            ${cuisines.map(c => `
                                <span class="filter-chip cuisine-chip" data-cuisine="${c}">${c}</span>
                            `).join('')}
                        </div>
                    </div>
                `).join('')}
            </div>`;
        container.appendChild(cuisineGroup);

        // Dietary tags
        const dietGroup = document.createElement('div');
        dietGroup.className = 'd-flex flex-wrap gap-1';
        f.dietary_tags.forEach(tag => {
            const chip = document.createElement('span');
            chip.className = 'filter-chip dietary-chip';
            chip.dataset.tag = tag;
            chip.textContent = tag;
            chip.addEventListener('click', () => {
                chip.classList.toggle('tag-active');
                onFilterChange();
            });
            dietGroup.appendChild(chip);
        });
        container.appendChild(dietGroup);

        // Max time input
        const timeGroup = document.createElement('div');
        timeGroup.className = 'input-group input-group-sm';
        timeGroup.style.maxWidth = '180px';
        timeGroup.innerHTML = `
            <span class="input-group-text"><i class="bi bi-clock"></i></span>
            <input type="number" class="form-control" id="filterMaxTime" placeholder="最大耗时(分钟)" min="1">`;
        container.appendChild(timeGroup);

        // Sort buttons — inline radio group
        const sortGroup = document.createElement('div');
        sortGroup.className = 'btn-group btn-group-sm sort-group';
        sortGroup.role = 'group';
        sortGroup.innerHTML = `
            <input type="radio" class="btn-check" name="sortBy" id="sortMatch" value="match" checked>
            <label class="btn btn-outline-primary" for="sortMatch">匹配度</label>
            <input type="radio" class="btn-check" name="sortBy" id="sortTime" value="time">
            <label class="btn btn-outline-primary" for="sortTime">耗时</label>
            <input type="radio" class="btn-check" name="sortBy" id="sortCalories" value="calories">
            <label class="btn btn-outline-primary" for="sortCalories">热量</label>`;

        // Wrap sort in a container for consistent spacing
        const sortWrapper = document.createElement('div');
        sortWrapper.appendChild(sortGroup);
        container.appendChild(sortWrapper);

        // Attach change listeners for sort and time
        sortGroup.querySelectorAll('input').forEach(inp => {
            inp.addEventListener('change', onFilterChange);
        });
        $('#filterMaxTime')?.addEventListener('change', onFilterChange);
    }

    function getActiveCuisines() {
        return [...$$('.cuisine-chip.active')].map(el => el.dataset.cuisine);
    }
    function getActiveDietary() {
        return [...$$('.dietary-chip.tag-active')].map(el => el.dataset.tag);
    }
    function getActiveSort() {
        const checked = document.querySelector('input[name="sortBy"]:checked');
        return checked ? checked.value : 'match';
    }
    function getActiveMaxTime() {
        const inp = $('#filterMaxTime');
        if (!inp || !inp.value) return null;
        return parseInt(inp.value) || null;
    }

    // ─────────────────────────────────────────────
    // PAGE: Search
    // ─────────────────────────────────────────────
    function renderSearchPage() {
        appEl.innerHTML = `
            <div class="hero-section">
                <div class="search-card">
                    <div class="search-title"><i class="bi bi-search-heart me-2"></i>输入你拥有的食材</div>
                    <div id="searchTagInput"></div>
                    <div class="d-flex align-items-center gap-3 mt-3 flex-wrap">
                        <div class="form-check form-switch sub-toggle">
                            <input class="form-check-input" type="checkbox" id="allowSub">
                            <label class="form-check-label" for="allowSub">允许食材替换</label>
                        </div>
                        <button class="btn btn-primary ms-auto" id="btnSearch">
                            <i class="bi bi-search me-1"></i>开始查找
                        </button>
                    </div>
                </div>
            </div>
            <div class="filters-bar" id="filtersBar"></div>
            <div id="searchResults"></div>`;

        const tagInput = createTagInput($('#searchTagInput'), state.ingredients);
        // Attach state sync
        tagInput._sync = () => { state.ingredients = tagInput.getTags(); };

        loadFilters().then(() => {
            renderFiltersBar($('#filtersBar'), () => {
                if (state.lastSearchParams) doSearch(state.lastSearchParams.ingredients);
            });
        });

        // Sub toggle
        const subToggle = $('#allowSub');
        subToggle.checked = state.lastSearchParams?.allow_substitution || false;

        // Search button
        $('#btnSearch').addEventListener('click', () => {
            tagInput._sync();
            if (state.ingredients.length === 0) {
                showToast('请先输入食材', 'error');
                return;
            }
            doSearch(state.ingredients.join(','));
        });

        // Enter key in the tag input triggers search
        const tagAreaInput = $('#searchTagInput').querySelector('input');
        if (tagAreaInput) {
            tagAreaInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && e.ctrlKey) {
                    tagInput._sync();
                    if (state.ingredients.length > 0) doSearch(state.ingredients.join(','));
                }
            });
        }

        // Show previous results if any
        if (state.searchResults) {
            displaySearchResults(state.searchResults);
        }
    }

    async function doSearch(ingredients) {
        showLoading();
        try {
            const params = {
                ingredients: ingredients,
                allow_substitution: $('#allowSub')?.checked || false,
                max_time: getActiveMaxTime(),
                cuisine_list: getActiveCuisines().length > 0 ? getActiveCuisines() : null,
                dietary_list: getActiveDietary().length > 0 ? getActiveDietary() : null,
                sort_by: getActiveSort(),
                top_n: 10,
            };
            state.lastSearchParams = params;

            const data = await api('/api/search', {
                method: 'POST',
                body: JSON.stringify(params),
            });
            state.searchResults = data;
            displaySearchResults(data);
        } catch (err) {
            showToast(err.message, 'error');
        } finally {
            hideLoading();
        }
    }

    function displaySearchResults(data) {
        const container = $('#searchResults');
        if (!container) return;
        container.innerHTML = '';

        if (!data.results || data.results.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="bi bi-emoji-frown"></i>
                    <p>没有找到匹配的菜谱，试试其他食材吧</p>
                </div>`;
            return;
        }

        // Summary
        const summary = document.createElement('div');
        summary.className = 'section-header mt-3';
        const totalStr = data.total_count > data.results.length
            ? `共 ${data.total_count} 个结果，显示前 ${data.results.length} 条`
            : `找到 ${data.total_count} 个符合条件的菜谱`;
        summary.innerHTML = `<h5><i class="bi bi-list-check me-2"></i>${totalStr}</h5>`;
        container.appendChild(summary);

        data.results.forEach((info, idx) => {
            const recipe = info.recipe;
            const card = document.createElement('div');
            card.className = 'recipe-card d-flex gap-3 align-items-start';

            const ratio = info.match_ratio;
            const pct = formatPct(ratio);
            const mc = matchClass(ratio);

            // Sub items
            let subStr = '';
            if (info.sub_items && Object.keys(info.sub_items).length > 0) {
                const subs = Object.entries(info.sub_items).map(([rcp, user]) => `${user}→${rcp}`);
                subStr = `<span class="badge-sub ms-2">替换: ${subs.join('、')}</span>`;
            }

            const missingMain = info.missing_main || [];
            const missingSeas = info.missing_seasonings || [];
            let missingStr = '';
            if (missingMain.length) missingStr += `<span>还需主料: ${missingMain.join('、')}</span> `;
            if (missingSeas.length) missingStr += `<span class="text-muted-2">还需调料: ${missingSeas.join('、')}</span>`;

            const totalTime = (recipe.prep_time || 0) + (recipe.cook_time || 0);
            const calories = recipe.nutrition?.calories || 0;
            const tags = recipe.dietary_tags || [];

            card.innerHTML = `
                <div class="recipe-rank">#${idx + 1}</div>
                <div class="flex-grow-1">
                    <div class="d-flex align-items-center flex-wrap gap-2 mb-1">
                        <span class="recipe-name">${recipe.name}</span>
                        <span class="match-badge ${mc}">${pct}</span>
                        ${subStr}
                    </div>
                    <div class="recipe-meta">
                        <span><i class="bi bi-clock"></i> ${totalTime}分钟</span>
                        <span><i class="bi bi-fire"></i> ${calories.toFixed(0)} kcal</span>
                        <span><i class="bi bi-geo-alt"></i> ${recipe.cuisine || '未知'}</span>
                        ${tags.map(t => `<span class="badge bg-light text-dark">${t}</span>`).join('')}
                    </div>
                    ${missingStr ? `<div class="recipe-missing">${missingStr}</div>` : ''}
                </div>
                <div class="text-end flex-shrink-0">
                    <button class="btn btn-sm btn-outline-primary recipe-detail-btn" data-id="${recipe.id}">
                        <i class="bi bi-info-circle"></i> 详情
                    </button>
                </div>`;

            // Click card to open detail (except when clicking the detail button)
            card.addEventListener('click', (e) => {
                if (!e.target.closest('.recipe-detail-btn')) {
                    openRecipeDetail(recipe.id);
                }
            });
            card.querySelector('.recipe-detail-btn').addEventListener('click', (e) => {
                e.stopPropagation();
                openRecipeDetail(recipe.id);
            });

            container.appendChild(card);
        });
    }

    // ─────────────────────────────────────────────
    // Recipe Detail Modal
    // ─────────────────────────────────────────────
    async function openRecipeDetail(recipeId) {
        getBsModal().show();
        recipeModalContent.innerHTML = `
            <div class="modal-body text-center py-5">
                <div class="spinner-border text-primary" role="status"></div>
                <p class="mt-3">加载菜谱详情...</p>
            </div>`;

        try {
            const data = await api(`/api/recipes/${recipeId}`);
            const recipe = data.recipe;
            const totalTime = (recipe.prep_time || 0) + (recipe.cook_time || 0);
            const calories = recipe.nutrition?.calories || 0;
            const tags = recipe.dietary_tags || [];

            recipeModalContent.innerHTML = `
                <div class="modal-header">
                    <h5 class="modal-title fw-bold">${recipe.name}</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                    <div class="d-flex flex-wrap gap-3 mb-3 text-muted">
                        <span><i class="bi bi-clock"></i> 准备 ${recipe.prep_time || 0}分钟 + 烹饪 ${recipe.cook_time || 0}分钟</span>
                        <span><i class="bi bi-fire"></i> ${calories.toFixed(0)} kcal</span>
                        <span><i class="bi bi-geo-alt"></i> ${recipe.cuisine || '未知'}</span>
                    </div>
                    ${tags.length ? `<div class="mb-3">${tags.map(t => `<span class="badge bg-light text-dark me-1">${t}</span>`).join('')}</div>` : ''}

                    <h6 class="fw-bold mt-3"><i class="bi bi-basket me-2"></i>材料</h6>
                    <ul class="list-unstyled">
                        ${(recipe.ingredients || []).map(ing => `
                            <li class="mb-1">• ${ing.name} — ${ing.quantity || '适量'}</li>
                        `).join('')}
                    </ul>

                    <h6 class="fw-bold mt-3"><i class="bi bi-list-ol me-2"></i>制作步骤</h6>
                    ${(recipe.steps || []).map((step, i) => `
                        <div class="step-item d-flex gap-2">
                            <span class="fw-bold text-primary">${i + 1}.</span>
                            <span>${step}</span>
                        </div>
                    `).join('')}

                    ${recipe.nutrition ? `
                        <h6 class="fw-bold mt-3"><i class="bi bi-bar-chart me-2"></i>营养成分</h6>
                        <div class="row row-cols-2 row-cols-md-4 g-2">
                            <div class="col"><div class="bg-light rounded-3 p-2 text-center"><small class="text-muted">热量</small><br><strong>${recipe.nutrition.calories?.toFixed(0) || '-'} kcal</strong></div></div>
                            <div class="col"><div class="bg-light rounded-3 p-2 text-center"><small class="text-muted">蛋白质</small><br><strong>${recipe.nutrition.protein || '-'} g</strong></div></div>
                            <div class="col"><div class="bg-light rounded-3 p-2 text-center"><small class="text-muted">脂肪</small><br><strong>${recipe.nutrition.fat || '-'} g</strong></div></div>
                            <div class="col"><div class="bg-light rounded-3 p-2 text-center"><small class="text-muted">碳水</small><br><strong>${recipe.nutrition.carbs || '-'} g</strong></div></div>
                        </div>
                    ` : ''}

                    <div class="d-flex gap-2 mt-4 flex-wrap">
                        <button class="btn btn-outline-primary btn-sm" id="btnShopping">
                            <i class="bi bi-cart"></i> 购物清单
                        </button>
                        <button class="btn btn-outline-primary btn-sm" id="btnScale">
                            <i class="bi bi-arrows-angle-expand"></i> 缩放配方
                        </button>
                        <button class="btn btn-outline-warning btn-sm" id="btnFav">
                            <i class="bi ${recipe.is_favorite ? 'bi-heart-fill' : 'bi-heart'}"></i> ${recipe.is_favorite ? '取消收藏' : '收藏'}
                        </button>
                    </div>
                    <div id="shoppingResult" class="mt-3"></div>
                    <div id="scaleResult" class="mt-3"></div>
                </div>`;

            // Shopping list button
            recipeModalContent.querySelector('#btnShopping').addEventListener('click', async () => {
                const btn = recipeModalContent.querySelector('#btnShopping');
                btn.disabled = true;
                btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> 加载中...';
                try {
                    const userIngs = state.lastSearchParams?.ingredients || '';
                    const shopData = await api(`/api/shopping?recipe_id=${recipeId}&ingredients=${encodeURIComponent(userIngs)}&include_seasonings=true`, { method: 'POST' });
                    const resultEl = recipeModalContent.querySelector('#shoppingResult');
                    if (!shopData.shopping || shopData.shopping.length === 0) {
                        resultEl.innerHTML = '<div class="alert alert-success py-2">所有材料您都已具备！</div>';
                    } else {
                        resultEl.innerHTML = `
                            <h6 class="fw-bold mt-2"><i class="bi bi-cart-check me-2"></i>购物清单</h6>
                            ${shopData.shopping.map(item => `
                                <div class="shopping-item">
                                    <span>${item.name} ${item.quantity || ''}</span>
                                    <span class="item-tag ${item.is_seasoning ? 'tag-seasoning' : 'tag-main'}">${item.is_seasoning ? '调料' : '主料'}</span>
                                </div>
                            `).join('')}`;
                    }
                } catch (err) {
                    showToast(err.message, 'error');
                } finally {
                    btn.disabled = false;
                    btn.innerHTML = '<i class="bi bi-cart"></i> 购物清单';
                }
            });

            // Scale button
            recipeModalContent.querySelector('#btnScale').addEventListener('click', async () => {
                const factor = parseFloat(prompt('请输入缩放倍数（如 2 表示双倍，0.5 表示减半）:', ''));
                if (!factor || factor <= 0) return;
                try {
                    const scaleData = await api('/api/scale', {
                        method: 'POST',
                        body: JSON.stringify({ recipe_id: recipeId, factor }),
                    });
                    const scaled = scaleData.scaled;
                    const resultEl = recipeModalContent.querySelector('#scaleResult');
                    resultEl.innerHTML = `
                        <h6 class="fw-bold mt-2"><i class="bi bi-arrows-angle-expand me-2"></i>缩放后配方 (×${factor})</h6>
                        <ul class="list-unstyled">
                            ${(scaled.ingredients || []).map(ing => `
                                <li>• ${ing.name} — ${ing.quantity || '适量'}</li>
                            `).join('')}
                        </ul>`;
                } catch (err) {
                    showToast(err.message, 'error');
                }
            });

            // Favorite toggle
            recipeModalContent.querySelector('#btnFav').addEventListener('click', async () => {
                try {
                    await api('/api/favorites/toggle', {
                        method: 'POST',
                        body: JSON.stringify({ recipe_id: recipeId }),
                    });
                    const btn = recipeModalContent.querySelector('#btnFav');
                    const isFav = btn.innerHTML.includes('bi-heart-fill');
                    if (isFav) {
                        btn.innerHTML = '<i class="bi bi-heart"></i> 收藏';
                    } else {
                        btn.innerHTML = '<i class="bi bi-heart-fill"></i> 取消收藏';
                    }
                    showToast(isFav ? '已取消收藏' : '已添加到收藏');
                } catch (err) {
                    showToast(err.message, 'error');
                }
            });

        } catch (err) {
            recipeModalContent.innerHTML = `
                <div class="modal-body text-center py-5 text-danger">
                    <i class="bi bi-exclamation-triangle" style="font-size: 2rem;"></i>
                    <p class="mt-3">加载失败: ${err.message}</p>
                </div>`;
        }
    }

    // ─────────────────────────────────────────────
    // PAGE: Weekly Plan
    // ─────────────────────────────────────────────
    function renderWeeklyPlanPage() {
        appEl.innerHTML = `
            <div class="search-card mb-4">
                <div class="search-title"><i class="bi bi-calendar-week me-2"></i>一周推荐计划</div>
                <div id="weeklyTagInput"></div>
                <div class="d-flex align-items-center gap-3 mt-3 flex-wrap">
                    <div class="form-check form-switch sub-toggle">
                        <input class="form-check-input" type="checkbox" id="weeklyAllowSub">
                        <label class="form-check-label" for="weeklyAllowSub">允许食材替换</label>
                    </div>
                    <div class="input-group input-group-sm" style="max-width: 180px;">
                        <span class="input-group-text">天数</span>
                        <input type="number" class="form-control" id="planDays" value="3" min="1" max="14">
                    </div>
                    <button class="btn btn-primary ms-auto" id="btnPlan">
                        <i class="bi bi-magic me-1"></i>生成计划
                    </button>
                </div>
            </div>
            <div id="planResults"></div>
            <div id="planShopping" class="mt-3"></div>`;

        const tagInput = createTagInput($('#weeklyTagInput'), state.ingredients.length > 0 ? state.ingredients : []);

        $('#btnPlan').addEventListener('click', async () => {
            const tags = tagInput.getTags();
            if (tags.length === 0) {
                showToast('请先输入食材', 'error');
                return;
            }
            state.ingredients = tags;
            showLoading();
            try {
                const data = await api('/api/weekly-plan', {
                    method: 'POST',
                    body: JSON.stringify({
                        ingredients: tags.join(','),
                        allow_substitution: $('#weeklyAllowSub')?.checked || false,
                        num_days: parseInt($('#planDays').value) || 3,
                    }),
                });
                state.planResults = data;
                state.planUserNormalized = data.user_normalized;
                displayPlan(data);
            } catch (err) {
                showToast(err.message, 'error');
            } finally {
                hideLoading();
            }
        });

        if (state.planResults) {
            displayPlan(state.planResults);
        }
    }

    function displayPlan(data) {
        const container = $('#planResults');
        if (!container) return;
        container.innerHTML = '';

        if (!data.plan || data.plan.length === 0) {
            container.innerHTML = '<div class="empty-state"><i class="bi bi-emoji-frown"></i><p>未能生成任何推荐菜谱</p></div>';
            return;
        }

        container.innerHTML = `<h5 class="fw-bold mb-3"><i class="bi bi-list-check me-2"></i>共 ${data.plan.length} 道推荐菜谱</h5>`;

        data.plan.forEach((detail, idx) => {
            const recipe = detail.recipe;
            const dayCard = document.createElement('div');
            dayCard.className = 'plan-day-card';
            const totalTime = (recipe.prep_time || 0) + (recipe.cook_time || 0);
            const calories = recipe.nutrition?.calories || 0;
            const pct = formatPct(detail.score);
            let subStr = '';
            if (detail.sub_items && Object.keys(detail.sub_items).length > 0) {
                const subs = Object.entries(detail.sub_items).map(([rcp, user]) => `${user}→${rcp}`);
                subStr = `<span class="badge-sub ms-2">替换: ${subs.join('、')}</span>`;
            }

            dayCard.innerHTML = `
                <div class="day-number">第 ${idx + 1} 天</div>
                <div class="d-flex align-items-start justify-content-between flex-wrap gap-2 mt-1">
                    <div>
                        <span class="fw-bold fs-5">${recipe.name}</span>
                        <span class="match-badge ${matchClass(detail.score)} ms-2">${pct}</span>
                        ${subStr}
                        <div class="recipe-meta">
                            <span><i class="bi bi-clock"></i> ${totalTime}分钟</span>
                            <span><i class="bi bi-fire"></i> ${calories.toFixed(0)} kcal</span>
                            <span><i class="bi bi-geo-alt"></i> ${recipe.cuisine || '未知'}</span>
                        </div>
                    </div>
                    <div class="d-flex gap-2 align-items-start">
                        <label class="form-check">
                            <input class="form-check-input plan-checkbox" type="checkbox" data-idx="${idx}" checked>
                        </label>
                        <button class="btn btn-sm btn-outline-primary recipe-detail-btn" data-id="${recipe.id}">
                            <i class="bi bi-info-circle"></i> 详情
                        </button>
                    </div>
                </div>`;

            dayCard.querySelector('.recipe-detail-btn').addEventListener('click', (e) => {
                e.stopPropagation();
                openRecipeDetail(recipe.id);
            });
            container.appendChild(dayCard);
        });

        // Merged shopping list button
        const shopBtn = document.createElement('button');
        shopBtn.className = 'btn btn-primary mt-3';
        shopBtn.innerHTML = '<i class="bi bi-cart-check me-1"></i>生成合并购物清单';
        shopBtn.addEventListener('click', () => generateMergedShopping(data));
        container.appendChild(shopBtn);
    }

    async function generateMergedShopping(data) {
        const checked = [...$$('.plan-checkbox:checked')].map(el => parseInt(el.dataset.idx));
        const selected = data.plan.filter((_, i) => checked.includes(i));
        if (selected.length === 0) {
            showToast('请至少选择一道菜', 'error');
            return;
        }

        const merged = {};
        const userIngs = state.lastSearchParams?.ingredients || state.ingredients.join(',') || '';

        for (const detail of selected) {
            try {
                const shopData = await api(`/api/shopping?recipe_id=${detail.recipe.id}&ingredients=${encodeURIComponent(userIngs)}&include_seasonings=true`, { method: 'POST' });
                for (const item of (shopData.shopping || [])) {
                    const key = item.name;
                    if (!merged[key]) merged[key] = item;
                }
            } catch (e) { /* skip err */ }
        }

        const container = $('#planShopping');
        if (!container) return;
        if (Object.keys(merged).length === 0) {
            container.innerHTML = '<div class="alert alert-success">您已具备所选菜品的所有食材！</div>';
            return;
        }

        container.innerHTML = `
            <div class="card p-3 mt-3">
                <h6 class="fw-bold"><i class="bi bi-cart-check me-2"></i>合并购物清单（${selected.length} 道菜品，${Object.keys(merged).length} 项）</h6>
                ${Object.values(merged).map(item => `
                    <div class="shopping-item">
                        <span>${item.name} ${item.quantity || ''}</span>
                        <span class="item-tag ${item.is_seasoning ? 'tag-seasoning' : 'tag-main'}">${item.is_seasoning ? '调料' : '主料'}</span>
                    </div>
                `).join('')}
            </div>`;
    }

    // ─────────────────────────────────────────────
    // PAGE: Rate Recipes
    // ─────────────────────────────────────────────
    async function renderRatePage() {
        appEl.innerHTML = `
            <div class="search-card">
                <div class="search-title"><i class="bi bi-star me-2"></i>给菜谱评分</div>
                <div class="input-group mb-3">
                    <span class="input-group-text"><i class="bi bi-search"></i></span>
                    <input type="text" class="form-control" id="rateSearch" placeholder="搜索菜谱名称...">
                </div>
                <div id="rateList" style="max-height: 60vh; overflow-y: auto;"></div>
            </div>`;

        showLoading();
        try {
            const data = await api('/api/recipes');
            state.allRecipes = data.recipes;
            displayRateList(state.allRecipes);
        } catch (err) {
            showToast(err.message, 'error');
        } finally {
            hideLoading();
        }

        $('#rateSearch').addEventListener('input', (e) => {
            const q = e.target.value.trim().toLowerCase();
            const filtered = q ? state.allRecipes.filter(r => r.name.toLowerCase().includes(q)) : state.allRecipes;
            displayRateList(filtered);
        });
    }

    function displayRateList(recipes) {
        const container = $('#rateList');
        if (!container) return;
        container.innerHTML = '';

        if (recipes.length === 0) {
            container.innerHTML = '<p class="text-muted text-center py-3">没有找到菜谱</p>';
            return;
        }

        recipes.slice(0, 100).forEach(r => {
            const item = document.createElement('div');
            item.className = 'recipe-list-item';
            const stars = '★'.repeat(Math.round(r.rating)) + '☆'.repeat(5 - Math.round(r.rating));
            item.innerHTML = `
                <div class="flex-grow-1">
                    <span class="fw-bold">${r.name}</span>
                    <span class="text-muted ms-2 small">${r.cuisine || ''}</span>
                    <span class="badge ms-2 ${r.is_favorite ? 'bg-danger' : 'bg-light text-dark'}">${r.is_favorite ? '★ 已收藏' : ''}</span>
                </div>
                <div class="d-flex align-items-center gap-3">
                    <span class="star-rating">${stars} <small class="text-muted">(${r.ratings_count})</small></span>
                    <div class="btn-group btn-group-sm">
                        ${[1,2,3,4,5].map(s => `
                            <button class="btn btn-outline-warning rate-star-btn" data-id="${r.id}" data-score="${s}">${s}</button>
                        `).join('')}
                    </div>
                </div>`;
            container.appendChild(item);
        });

        // Attach rating buttons
        container.querySelectorAll('.rate-star-btn').forEach(btn => {
            btn.addEventListener('click', async () => {
                const recipeId = btn.dataset.id;
                const score = parseInt(btn.dataset.score);
                try {
                    await api('/api/rate', {
                        method: 'POST',
                        body: JSON.stringify({ recipe_id: recipeId, score }),
                    });
                    showToast(`评分成功：${score} 星！`);
                    // Refresh list
                    const data = await api('/api/recipes');
                    state.allRecipes = data.recipes;
                    const q = $('#rateSearch')?.value?.trim()?.toLowerCase() || '';
                    const filtered = q ? state.allRecipes.filter(r => r.name.toLowerCase().includes(q)) : state.allRecipes;
                    displayRateList(filtered);
                } catch (err) {
                    showToast(err.message, 'error');
                }
            });
        });
    }

    // ─────────────────────────────────────────────
    // PAGE: Favorites
    // ─────────────────────────────────────────────
    async function renderFavoritesPage() {
        appEl.innerHTML = `
            <div class="search-card">
                <div class="search-title"><i class="bi bi-heart me-2"></i>收藏夹管理</div>
                <div class="d-flex gap-2 mb-3 flex-wrap">
                    <button class="btn btn-outline-primary btn-sm" id="btnExportFav"><i class="bi bi-download"></i> 导出</button>
                    <button class="btn btn-outline-primary btn-sm" id="btnImportFav"><i class="bi bi-upload"></i> 导入</button>
                    <button class="btn btn-outline-primary btn-sm" id="btnAddFav"><i class="bi bi-plus-circle"></i> 添加收藏</button>
                </div>
                <div id="favList" style="max-height: 60vh; overflow-y: auto;"></div>
                <div id="favAddArea" class="mt-3 d-none"></div>
            </div>`;

        await loadFavorites();

        $('#btnExportFav').addEventListener('click', async () => {
            try {
                const data = await api('/api/favorites/export', { method: 'POST', body: JSON.stringify({}) });
                showToast(`导出成功：${data.count} 道收藏菜谱 → ${data.filepath}`);
            } catch (err) { showToast(err.message, 'error'); }
        });

        $('#btnImportFav').addEventListener('click', async () => {
            const filepath = prompt('请输入要导入的 JSON 文件路径:', 'data/favorites.json');
            if (!filepath) return;
            try {
                const data = await api('/api/favorites/import', {
                    method: 'POST',
                    body: JSON.stringify({ filepath }),
                });
                showToast(`导入成功：新增 ${data.count} 道收藏菜谱`);
                await loadFavorites();
            } catch (err) { showToast(err.message, 'error'); }
        });

        $('#btnAddFav').addEventListener('click', async () => {
            const area = $('#favAddArea');
            if (area.classList.contains('d-none')) {
                area.classList.remove('d-none');
                if (state.allRecipes.length === 0) {
                    try { state.allRecipes = (await api('/api/recipes')).recipes; } catch (e) {}
                }
                area.innerHTML = `
                    <h6>选择要收藏的菜谱</h6>
                    <div id="addFavList" style="max-height: 300px; overflow-y: auto;">
                        ${state.allRecipes.slice(0, 50).map(r => `
                            <div class="recipe-list-item">
                                <span class="fw-bold">${r.name}</span>
                                <span class="text-muted small">${r.cuisine || ''}</span>
                                ${r.is_favorite
                                    ? '<span class="badge bg-danger">已收藏</span>'
                                    : `<button class="btn btn-sm btn-outline-danger add-fav-btn" data-id="${r.id}">收藏</button>`}
                            </div>
                        `).join('')}
                    </div>`;
                area.querySelectorAll('.add-fav-btn').forEach(btn => {
                    btn.addEventListener('click', async () => {
                        try {
                            await api('/api/favorites/toggle', {
                                method: 'POST',
                                body: JSON.stringify({ recipe_id: btn.dataset.id }),
                            });
                            showToast('添加收藏成功！');
                            await loadFavorites();
                            btn.outerHTML = '<span class="badge bg-danger">已收藏</span>';
                        } catch (err) { showToast(err.message, 'error'); }
                    });
                });
            } else {
                area.classList.add('d-none');
            }
        });
    }

    async function loadFavorites() {
        const container = $('#favList');
        if (!container) return;
        try {
            const data = await api('/api/favorites');
            if (data.favorites.length === 0) {
                container.innerHTML = '<p class="text-muted text-center py-3">收藏夹为空</p>';
                return;
            }
            container.innerHTML = data.favorites.map(r => `
                <div class="recipe-list-item">
                    <div class="flex-grow-1">
                        <span class="fw-bold">${r.name}</span>
                        <span class="text-muted ms-2 small">${r.cuisine || ''}</span>
                        <span class="ms-2">⭐ ${r.rating?.toFixed(1) || '-'}</span>
                    </div>
                    <div class="d-flex gap-2 align-items-center">
                        <button class="btn btn-sm btn-outline-primary recipe-detail-btn" data-id="${r.id}">
                            <i class="bi bi-info-circle"></i> 详情
                        </button>
                        <button class="btn btn-sm btn-outline-danger remove-fav-btn" data-id="${r.id}">
                            <i class="bi bi-trash"></i> 移除
                        </button>
                    </div>
                </div>
            `).join('');

            container.querySelectorAll('.recipe-detail-btn').forEach(btn => {
                btn.addEventListener('click', () => openRecipeDetail(btn.dataset.id));
            });
            container.querySelectorAll('.remove-fav-btn').forEach(btn => {
                btn.addEventListener('click', async () => {
                    try {
                        await api('/api/favorites/toggle', {
                            method: 'POST',
                            body: JSON.stringify({ recipe_id: btn.dataset.id }),
                        });
                        showToast('已移除收藏');
                        await loadFavorites();
                    } catch (err) { showToast(err.message, 'error'); }
                });
            });
        } catch (err) {
            showToast(err.message, 'error');
        }
    }

    // ─────────────────────────────────────────────
    // Init — Load filters, render the search page
    // ─────────────────────────────────────────────
    async function loadFilters() {
        if (state.filters) return;
        try {
            state.filters = await api('/api/filters');
        } catch (err) {
            console.error('Failed to load filters:', err);
        }
    }

    // Initial page render
    loadFilters().then(() => navigate('search'));

})();