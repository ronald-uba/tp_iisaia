/* ============================================================
 * BookShelf — lógica de UI
 *
 * Convenciones (CLAUDE.md):
 *   - Sin imports, sin módulos ES, sin librerías externas.
 *   - camelCase para variables y funciones.
 *   - Llamadas a la API en funciones con prefijo `api`.
 *   - Funciones render* producen HTML; eventos se enganchan con
 *     addEventListener tras renderizar.
 *   - El estado vive en variables a nivel de módulo.
 * ============================================================ */

(function () {
  "use strict";

  // -------------------------------------------------------------
  // Estado
  // -------------------------------------------------------------

  const API_BASE = "/api";

  /** @type {Array<Object>} */
  let booksCache = [];
  /** @type {Object|null} */
  let currentBook = null;
  /** @type {string} */
  let currentQuery = "";

  // -------------------------------------------------------------
  // Referencias al DOM (cacheadas al cargar)
  // -------------------------------------------------------------

  const $ = (sel) => document.querySelector(sel);

  const listView = $("#list-view");
  const detailView = $("#detail-view");

  const booksListEl = $("#books-list");
  const booksEmptyEl = $("#books-empty");
  const searchEmptyEl = $("#search-empty");
  const searchSummaryEl = $("#search-summary");
  const searchFormEl = $("#search-form");
  const searchInputEl = $("#search-input");
  const clearSearchBtn = $("#clear-search-btn");

  const bookFormEl = $("#book-form");
  const showBookFormBtn = $("#show-book-form-btn");
  const cancelBookFormBtn = $("#cancel-book-form-btn");

  const bookDetailEl = $("#book-detail");
  const editBookFormEl = $("#edit-book-form");
  const cancelEditBtn = $("#cancel-edit-btn");
  const backBtn = $("#back-btn");

  const reviewsListEl = $("#reviews-list");
  const reviewsEmptyEl = $("#reviews-empty");
  const reviewFormEl = $("#review-form");

  const toastEl = $("#toast");

  // -------------------------------------------------------------
  // Cliente de API
  // -------------------------------------------------------------

  async function apiRequest(method, path, body) {
    const opts = { method, headers: {} };
    if (body !== undefined) {
      opts.headers["Content-Type"] = "application/json";
      opts.body = JSON.stringify(body);
    }
    const res = await fetch(API_BASE + path, opts);
    if (res.status === 204) return null;
    const text = await res.text();
    const payload = text ? JSON.parse(text) : null;
    if (!res.ok) {
      const detail =
        (payload && (payload.detail || JSON.stringify(payload))) ||
        `Error HTTP ${res.status}`;
      const err = new Error(typeof detail === "string" ? detail : "Error de API");
      err.status = res.status;
      err.payload = payload;
      throw err;
    }
    return payload;
  }

  function apiGetBooks(q) {
    if (q && q.trim()) {
      return apiRequest("GET", "/books?q=" + encodeURIComponent(q.trim()));
    }
    return apiRequest("GET", "/books");
  }
  function apiGetBook(id) {
    return apiRequest("GET", `/books/${id}`);
  }
  function apiCreateBook(data) {
    return apiRequest("POST", "/books", data);
  }
  function apiUpdateBook(id, data) {
    return apiRequest("PUT", `/books/${id}`, data);
  }
  function apiDeleteBook(id) {
    return apiRequest("DELETE", `/books/${id}`);
  }
  function apiGetReviews(bookId) {
    return apiRequest("GET", `/books/${bookId}/reviews`);
  }
  function apiCreateReview(bookId, data) {
    return apiRequest("POST", `/books/${bookId}/reviews`, data);
  }
  function apiDeleteReview(reviewId) {
    return apiRequest("DELETE", `/reviews/${reviewId}`);
  }

  // -------------------------------------------------------------
  // Utilidades
  // -------------------------------------------------------------

  /** Escapa HTML para evitar inyección al renderizar contenido del usuario. */
  function escapeHtml(str) {
    if (str === null || str === undefined) return "";
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function formatDate(iso) {
    if (!iso) return "";
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return "";
    return d.toLocaleDateString("es-AR", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  }

  function stars(rating) {
    const n = Math.max(0, Math.min(5, Number(rating) || 0));
    return "★".repeat(n) + "☆".repeat(5 - n);
  }

  let toastTimer = null;
  function showToast(message, kind) {
    toastEl.textContent = message;
    toastEl.classList.remove("hidden", "toast-success", "toast-error");
    toastEl.classList.add(kind === "error" ? "toast-error" : "toast-success");
    if (toastTimer) clearTimeout(toastTimer);
    toastTimer = setTimeout(() => toastEl.classList.add("hidden"), 3000);
  }

  function show(el) { el.classList.remove("hidden"); }
  function hide(el) { el.classList.add("hidden"); }

  // -------------------------------------------------------------
  // Render — lista de libros
  // -------------------------------------------------------------

  function renderBookList(books) {
    booksCache = books;
    booksListEl.innerHTML = books.map(renderBookCard).join("");
    // Mostrar el mensaje de vacío correcto según haya o no búsqueda activa.
    hide(booksEmptyEl);
    hide(searchEmptyEl);
    if (!books.length) {
      if (currentQuery) show(searchEmptyEl);
      else show(booksEmptyEl);
    }
    renderSearchSummary(books.length);
    // Enganchar clicks en cada tarjeta.
    booksListEl.querySelectorAll(".book-card").forEach((card) => {
      card.addEventListener("click", () => {
        const id = Number(card.dataset.bookId);
        openBookDetail(id);
      });
    });
  }

  function renderSearchSummary(count) {
    if (!currentQuery) {
      hide(searchSummaryEl);
      return;
    }
    const noun = count === 1 ? "resultado" : "resultados";
    searchSummaryEl.textContent =
      `${count} ${noun} para «${currentQuery}».`;
    show(searchSummaryEl);
  }

  function renderBookCard(book) {
    const year = book.published_year
      ? `<p class="book-year">📅 ${escapeHtml(book.published_year)}</p>`
      : "";
    return `
      <article class="book-card" data-book-id="${book.id}">
        <h3>${escapeHtml(book.title)}</h3>
        <p class="book-author">por ${escapeHtml(book.author)}</p>
        ${year}
        <div class="book-meta">Ver reseñas →</div>
      </article>
    `;
  }

  // -------------------------------------------------------------
  // Render — detalle de libro
  // -------------------------------------------------------------

  function renderBookDetail(book) {
    const year = book.published_year
      ? `<p class="book-year">📅 Publicado en ${escapeHtml(book.published_year)}</p>`
      : "";
    bookDetailEl.innerHTML = `
      <h2>${escapeHtml(book.title)}</h2>
      <p class="book-author">por ${escapeHtml(book.author)}</p>
      ${year}
      <div class="detail-actions">
        <button type="button" class="btn-edit" id="edit-book-btn">Editar</button>
        <button type="button" class="btn-danger" id="delete-book-btn">Eliminar libro</button>
      </div>
    `;
    $("#edit-book-btn").addEventListener("click", openEditForm);
    $("#delete-book-btn").addEventListener("click", handleDeleteBook);
  }

  // -------------------------------------------------------------
  // Render — reseñas
  // -------------------------------------------------------------

  function renderReviewList(reviews) {
    if (!reviews.length) {
      reviewsListEl.innerHTML = "";
      show(reviewsEmptyEl);
      return;
    }
    hide(reviewsEmptyEl);
    reviewsListEl.innerHTML = reviews.map(renderReviewItem).join("");
    reviewsListEl.querySelectorAll(".btn-delete-review").forEach((btn) => {
      btn.addEventListener("click", () => {
        const id = Number(btn.dataset.reviewId);
        handleDeleteReview(id);
      });
    });
  }

  function renderReviewItem(review) {
    return `
      <article class="review-card">
        <div class="review-head">
          <span class="reviewer-name">${escapeHtml(review.reviewer_name)}</span>
          <span class="review-stars" title="${review.rating} de 5">${stars(review.rating)}</span>
        </div>
        <p class="review-comment">${escapeHtml(review.comment)}</p>
        <div class="review-head">
          <span class="review-date">${formatDate(review.created_at)}</span>
          <button type="button" class="btn-danger btn-delete-review"
                  data-review-id="${review.id}">Eliminar</button>
        </div>
      </article>
    `;
  }

  // -------------------------------------------------------------
  // Acciones (handlers)
  // -------------------------------------------------------------

  async function loadBooks() {
    try {
      const books = await apiGetBooks(currentQuery);
      renderBookList(books);
    } catch (err) {
      showToast("No se pudo cargar la lista de libros: " + err.message, "error");
    }
  }

  function handleSearchSubmit(event) {
    event.preventDefault();
    currentQuery = searchInputEl.value.trim();
    loadBooks();
  }

  function handleClearSearch() {
    if (!currentQuery && !searchInputEl.value) return;
    searchInputEl.value = "";
    currentQuery = "";
    loadBooks();
    searchInputEl.focus();
  }

  async function openBookDetail(bookId) {
    try {
      const book = await apiGetBook(bookId);
      currentBook = book;
      hide(listView);
      show(detailView);
      hide(editBookFormEl);
      renderBookDetail(book);
      await loadReviews(bookId);
      window.scrollTo({ top: 0, behavior: "smooth" });
    } catch (err) {
      showToast("No se pudo abrir el libro: " + err.message, "error");
    }
  }

  function backToList() {
    currentBook = null;
    hide(detailView);
    show(listView);
    loadBooks();
  }

  async function loadReviews(bookId) {
    try {
      const reviews = await apiGetReviews(bookId);
      renderReviewList(reviews);
    } catch (err) {
      showToast("No se pudieron cargar las reseñas: " + err.message, "error");
    }
  }

  // ----- Crear libro -----

  function openBookForm() {
    bookFormEl.reset();
    show(bookFormEl);
    $("#book-title").focus();
  }
  function closeBookForm() {
    bookFormEl.reset();
    hide(bookFormEl);
  }

  async function handleCreateBook(event) {
    event.preventDefault();
    const yearRaw = $("#book-year").value.trim();
    const data = {
      title: $("#book-title").value.trim(),
      author: $("#book-author").value.trim(),
      published_year: yearRaw === "" ? null : Number(yearRaw),
    };
    try {
      const created = await apiCreateBook(data);
      showToast(`Libro «${created.title}» agregado.`, "success");
      closeBookForm();
      await loadBooks();
    } catch (err) {
      showToast("No se pudo crear el libro: " + err.message, "error");
    }
  }

  // ----- Editar libro -----

  function openEditForm() {
    if (!currentBook) return;
    $("#edit-title").value = currentBook.title;
    $("#edit-author").value = currentBook.author;
    $("#edit-year").value = currentBook.published_year ?? "";
    show(editBookFormEl);
  }
  function closeEditForm() {
    hide(editBookFormEl);
  }

  async function handleUpdateBook(event) {
    event.preventDefault();
    if (!currentBook) return;
    const yearRaw = $("#edit-year").value.trim();
    const data = {
      title: $("#edit-title").value.trim(),
      author: $("#edit-author").value.trim(),
      published_year: yearRaw === "" ? null : Number(yearRaw),
    };
    try {
      const updated = await apiUpdateBook(currentBook.id, data);
      currentBook = updated;
      renderBookDetail(updated);
      closeEditForm();
      showToast("Libro actualizado.", "success");
    } catch (err) {
      showToast("No se pudo actualizar: " + err.message, "error");
    }
  }

  // ----- Borrar libro -----

  async function handleDeleteBook() {
    if (!currentBook) return;
    const ok = window.confirm(
      `¿Eliminar «${currentBook.title}» y todas sus reseñas? Esta acción no se puede deshacer.`
    );
    if (!ok) return;
    try {
      await apiDeleteBook(currentBook.id);
      showToast("Libro eliminado.", "success");
      backToList();
    } catch (err) {
      showToast("No se pudo eliminar: " + err.message, "error");
    }
  }

  // ----- Crear reseña -----

  async function handleCreateReview(event) {
    event.preventDefault();
    if (!currentBook) return;
    const data = {
      reviewer_name: $("#reviewer-name").value.trim(),
      rating: Number($("#review-rating").value),
      comment: $("#review-comment").value.trim(),
    };
    try {
      await apiCreateReview(currentBook.id, data);
      reviewFormEl.reset();
      showToast("Reseña publicada.", "success");
      await loadReviews(currentBook.id);
    } catch (err) {
      showToast("No se pudo publicar la reseña: " + err.message, "error");
    }
  }

  // ----- Borrar reseña -----

  async function handleDeleteReview(reviewId) {
    const ok = window.confirm("¿Eliminar esta reseña?");
    if (!ok) return;
    try {
      await apiDeleteReview(reviewId);
      showToast("Reseña eliminada.", "success");
      if (currentBook) await loadReviews(currentBook.id);
    } catch (err) {
      showToast("No se pudo eliminar la reseña: " + err.message, "error");
    }
  }

  // -------------------------------------------------------------
  // Enganche de eventos persistentes (formularios y botones fijos)
  // -------------------------------------------------------------

  function bindEvents() {
    showBookFormBtn.addEventListener("click", openBookForm);
    cancelBookFormBtn.addEventListener("click", closeBookForm);
    bookFormEl.addEventListener("submit", handleCreateBook);

    searchFormEl.addEventListener("submit", handleSearchSubmit);
    clearSearchBtn.addEventListener("click", handleClearSearch);

    backBtn.addEventListener("click", backToList);
    cancelEditBtn.addEventListener("click", closeEditForm);
    editBookFormEl.addEventListener("submit", handleUpdateBook);

    reviewFormEl.addEventListener("submit", handleCreateReview);
  }

  // -------------------------------------------------------------
  // Bootstrap
  // -------------------------------------------------------------

  document.addEventListener("DOMContentLoaded", () => {
    bindEvents();
    loadBooks();
  });
})();
