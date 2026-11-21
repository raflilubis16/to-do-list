/**
 * Agenda - Calendar & Dashboard Logic
 * FullCalendar integration, Mini Calendar, Filters, Modal, and Event Detail Panel.
 */

document.addEventListener('DOMContentLoaded', () => {
    // State
    let calendar;
    let currentSelectedEventId = null;
    let miniCurrentDate = new Date();
    let activeFilters = {
        status: '',
        priority: '',
        category: 'ALL',
        search: ''
    };

    // DOM Elements
    const calendarEl = document.getElementById('mainCalendar');
    const miniCalendarGrid = document.getElementById('miniCalendarGrid');
    const miniCalendarTitle = document.getElementById('miniCalendarTitle');
    const globalSearchInput = document.getElementById('globalSearchInput');
    const priorityFilterSelect = document.getElementById('priorityFilterSelect');
    const statusFilterBtns = document.querySelectorAll('.filter-status-btn');
    const categoryCheckboxes = document.querySelectorAll('.category-checkbox');
    const upcomingEventsList = document.getElementById('upcomingEventsList');
    const upcomingBadge = document.getElementById('upcomingBadge');

    // Detail Panel Elements
    const detailContent = document.getElementById('eventDetailContent');
    const detailEmpty = document.getElementById('eventDetailEmpty');
    const detailTitle = document.getElementById('detailTitle');
    const detailCategoryBadge = document.getElementById('detailCategoryBadge');
    const detailPriorityBadge = document.getElementById('detailPriorityBadge');
    const detailStatusBadge = document.getElementById('detailStatusBadge');
    const detailTime = document.getElementById('detailTime');
    const detailDuration = document.getElementById('detailDuration');
    const detailLocation = document.getElementById('detailLocation');
    const detailLocationRow = document.getElementById('detailLocationRow');
    const detailDescription = document.getElementById('detailDescription');
    const detailRemindersList = document.getElementById('detailRemindersList');
    const toggleCompleteBtn = document.getElementById('toggleCompleteBtn');
    const toggleCompleteText = document.getElementById('toggleCompleteText');
    const editEventBtn = document.getElementById('editEventBtn');
    const deleteEventBtn = document.getElementById('deleteEventBtn');

    // Modal Elements
    const eventModal = document.getElementById('eventModal');
    const eventForm = document.getElementById('eventForm');
    const modalTitle = document.getElementById('modalTitle');
    const openNewEventModalBtn = document.getElementById('openNewEventModalBtn');
    const closeEventModalBtn = document.getElementById('closeEventModalBtn');
    const cancelEventModalBtn = document.getElementById('cancelEventModalBtn');
    const formEventId = document.getElementById('formEventId');
    const eventTitleInput = document.getElementById('eventTitleInput');
    const eventAllDayInput = document.getElementById('eventAllDayInput');
    const eventStartInput = document.getElementById('eventStartInput');
    const eventEndInput = document.getElementById('eventEndInput');
    const eventCategorySelect = document.getElementById('eventCategorySelect');
    const eventPrioritySelect = document.getElementById('eventPrioritySelect');
    const eventLocationInput = document.getElementById('eventLocationInput');
    const eventDescriptionInput = document.getElementById('eventDescriptionInput');
    const titleError = document.getElementById('titleError');
    const timeError = document.getElementById('timeError');

    // Delete Modal Elements
    const deleteConfirmModal = document.getElementById('deleteConfirmModal');
    const deleteEventTitlePreview = document.getElementById('deleteEventTitlePreview');
    const cancelDeleteBtn = document.getElementById('cancelDeleteBtn');
    const confirmDeleteBtn = document.getElementById('confirmDeleteBtn');

    // ==========================================
    //  1. Helper Functions
    // ==========================================

    function pad(n) {
        return String(n).padStart(2, '0');
    }

    function formatDateTimeLocal(date) {
        if (!date) return '';
        const d = new Date(date);
        return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
    }

    function formatIndonesianDate(dateStr, allDay = false) {
        if (!dateStr) return '';
        const d = new Date(dateStr);
        const options = {
            weekday: 'short',
            day: 'numeric',
            month: 'short',
            year: 'numeric',
            timeZone: 'Asia/Jakarta'
        };
        const datePart = d.toLocaleDateString('id-ID', options);
        if (allDay) return `${datePart} (Sepanjang hari)`;

        const timePart = d.toLocaleTimeString('id-ID', {
            hour: '2-digit',
            minute: '2-digit',
            timeZone: 'Asia/Jakarta'
        });
        return `${datePart} · ${timePart} WIB`;
    }

    // ==========================================
    //  2. FullCalendar Setup (F-01)
    // ==========================================

    calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        locale: 'id',
        firstDay: 1, // Senin sesuai Bab 9 wireframe
        headerToolbar: {
            left: 'prev,today,next',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridDay'
        },
        buttonText: {
            today: 'Hari ini',
            month: 'Bulan',
            week: 'Minggu',
            day: 'Hari'
        },
        height: '100%',
        nowIndicator: true,
        selectable: true,
        dayMaxEvents: 3,

        // Fetch events from Flask REST API
        events: async function (info, successCallback, failureCallback) {
            try {
                const params = new URLSearchParams({
                    start: info.startStr,
                    end: info.endStr
                });

                if (activeFilters.status) params.append('status', activeFilters.status);
                if (activeFilters.category && activeFilters.category !== 'ALL') params.append('category', activeFilters.category);
                if (activeFilters.search) params.append('q', activeFilters.search);

                const response = await fetch(`/api/events?${params.toString()}`);
                if (!response.ok) throw new Error('Gagal memuat event');
                const rawEvents = await response.json();

                // Format events for FullCalendar
                const events = rawEvents
                    .filter(ev => {
                        if (activeFilters.priority && ev.priority !== activeFilters.priority) {
                            return false;
                        }
                        return true;
                    })
                    .map(ev => {
                        const isDone = ev.status === 'selesai';
                        return {
                            id: ev.id,
                            title: ev.title,
                            start: ev.start_at,
                            end: ev.end_at,
                            allDay: ev.all_day,
                            backgroundColor: isDone ? '#94a3b8' : (ev.category_color || '#4f46e5'),
                            borderColor: isDone ? '#94a3b8' : (ev.category_color || '#4f46e5'),
                            textColor: '#ffffff',
                            classNames: isDone ? ['event-completed'] : [],
                            extendedProps: ev
                        };
                    });

                successCallback(events);
                updateUpcomingList(rawEvents);
            } catch (err) {
                console.error(err);
                failureCallback(err);
            }
        },

        // Click date on calendar -> Open new event modal (UC-03)
        dateClick: function (info) {
            openEventModalForCreate(info.date);
        },

        // Click event on calendar -> Show detail panel (UC-02)
        eventClick: function (info) {
            info.jsEvent.preventDefault();
            loadEventDetail(info.event.id);
        }
    });

    calendar.render();

    // ==========================================
    //  3. Mini Calendar (Sidebar)
    // ==========================================

    function renderMiniCalendar(targetDate) {
        const year = targetDate.getFullYear();
        const month = targetDate.getMonth();

        const monthNames = [
            'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
            'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember'
        ];
        miniCalendarTitle.textContent = `${monthNames[month]} ${year}`;

        miniCalendarGrid.innerHTML = '';

        const firstDayIndex = new Date(year, month, 1).getDay(); // 0 is Sunday
        const daysInMonth = new Date(year, month + 1, 0).getDate();
        const today = new Date();

        // Empty padding cells
        for (let i = 0; i < firstDayIndex; i++) {
            const blank = document.createElement('div');
            blank.className = 'py-1 text-slate-300';
            miniCalendarGrid.appendChild(blank);
        }

        // Days
        for (let day = 1; day <= daysInMonth; day++) {
            const btn = document.createElement('button');
            btn.type = 'button';
            btn.textContent = day;
            btn.className = 'py-1 w-7 h-7 mx-auto rounded-full flex items-center justify-center font-medium hover:bg-slate-100 transition text-slate-700';

            const isToday = (today.getFullYear() === year && today.getMonth() === month && today.getDate() === day);
            if (isToday) {
                btn.className = 'py-1 w-7 h-7 mx-auto rounded-full flex items-center justify-center font-semibold bg-indigo-600 text-white shadow-xs';
            }

            btn.addEventListener('click', () => {
                const target = new Date(year, month, day);
                calendar.gotoDate(target);
            });

            miniCalendarGrid.appendChild(btn);
        }
    }

    renderMiniCalendar(miniCurrentDate);

    document.getElementById('miniPrevBtn').addEventListener('click', () => {
        miniCurrentDate.setMonth(miniCurrentDate.getMonth() - 1);
        renderMiniCalendar(miniCurrentDate);
    });

    document.getElementById('miniNextBtn').addEventListener('click', () => {
        miniCurrentDate.setMonth(miniCurrentDate.getMonth() + 1);
        renderMiniCalendar(miniCurrentDate);
    });

    document.getElementById('miniTodayBtn').addEventListener('click', () => {
        miniCurrentDate = new Date();
        renderMiniCalendar(miniCurrentDate);
        calendar.today();
    });

    // ==========================================
    //  4. Event Detail Panel (UC-02, F-04)
    // ==========================================

    async function loadEventDetail(eventId) {
        try {
            const res = await fetch(`/api/events/${eventId}`);
            if (!res.ok) throw new Error('Event tidak ditemukan');
            const event = await res.json();
            currentSelectedEventId = event.id;

            detailTitle.textContent = event.title;

            // Status Badge
            const isDone = event.status === 'selesai';
            detailStatusBadge.textContent = event.status.toUpperCase();
            detailStatusBadge.className = isDone
                ? 'text-xs px-2.5 py-0.5 rounded-full font-semibold bg-emerald-100 text-emerald-800'
                : 'text-xs px-2.5 py-0.5 rounded-full font-semibold bg-indigo-50 text-indigo-700';
            detailStatusBadge.classList.remove('hidden');

            // Category Badge
            detailCategoryBadge.textContent = event.category_name;
            detailCategoryBadge.style.backgroundColor = isDone ? '#94a3b8' : event.category_color;

            // Priority Badge
            const pColors = {
                tinggi: 'bg-rose-100 text-rose-700',
                sedang: 'bg-amber-100 text-amber-700',
                rendah: 'bg-slate-100 text-slate-700'
            };
            detailPriorityBadge.className = `inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium ${pColors[event.priority] || pColors.sedang}`;
            detailPriorityBadge.textContent = `Prioritas ${event.priority}`;

            // Time & Duration
            detailTime.textContent = formatIndonesianDate(event.start_at, event.all_day);
            if (event.end_at && !event.all_day) {
                detailDuration.textContent = `s/d ${formatIndonesianDate(event.end_at)}`;
            } else {
                detailDuration.textContent = '';
            }

            // Location
            if (event.location) {
                detailLocation.textContent = event.location;
                detailLocationRow.classList.remove('hidden');
            } else {
                detailLocationRow.classList.add('hidden');
            }

            // Description / Notes
            if (event.description && event.description.trim()) {
                detailDescription.textContent = event.description;
            } else {
                detailDescription.innerHTML = '<span class="text-slate-400 italic">Tidak ada catatan</span>';
            }

            // Reminders List
            detailRemindersList.innerHTML = '';
            if (event.reminders && event.reminders.length > 0) {
                event.reminders.forEach(r => {
                    const li = document.createElement('li');
                    li.className = 'flex items-center justify-between text-xs py-1 px-2.5 rounded bg-slate-50 border border-slate-100';

                    let label = `${r.offset_minutes} menit sebelumnya`;
                    if (r.offset_minutes === 0) label = 'Saat event dimulai';
                    else if (r.offset_minutes === 10) label = '10 menit sebelumnya';
                    else if (r.offset_minutes === 30) label = '30 menit sebelumnya';
                    else if (r.offset_minutes === 60) label = '1 jam sebelumnya';
                    else if (r.offset_minutes === 1440) label = '1 hari sebelumnya';

                    li.innerHTML = `
                        <span class="flex items-center gap-2 text-slate-700">
                            <i class="fa-regular fa-bell text-indigo-500 text-[11px]"></i>
                            <span>${label}</span>
                        </span>
                        <span class="text-[10px] font-medium px-1.5 py-0.5 rounded ${r.status === 'delivered' ? 'bg-slate-200 text-slate-600' : (r.status === 'due' ? 'bg-rose-100 text-rose-700' : 'bg-indigo-50 text-indigo-600')}">
                            ${r.status}
                        </span>
                    `;
                    detailRemindersList.appendChild(li);
                });
            } else {
                detailRemindersList.innerHTML = '<li class="text-slate-400 italic text-[11px]">Tidak ada pengingat</li>';
            }

            // Toggle Complete Button styling
            if (isDone) {
                toggleCompleteBtn.className = 'flex-1 py-2 px-3 text-xs font-medium text-white rounded-lg transition flex items-center justify-center gap-1.5 shadow-xs bg-slate-600 hover:bg-slate-700';
                toggleCompleteText.textContent = 'Aktifkan Kembali';
            } else {
                toggleCompleteBtn.className = 'flex-1 py-2 px-3 text-xs font-medium text-white rounded-lg transition flex items-center justify-center gap-1.5 shadow-xs bg-emerald-600 hover:bg-emerald-700';
                toggleCompleteText.textContent = 'Selesai';
            }

            // Show panel
            detailEmpty.classList.add('hidden');
            detailContent.classList.remove('hidden');
        } catch (err) {
            console.error(err);
        }
    }

    // Toggle Complete Action (UC-06, F-05)
    toggleCompleteBtn.addEventListener('click', async () => {
        if (!currentSelectedEventId) return;
        try {
            const res = await fetch(`/api/events/${currentSelectedEventId}/status`, {
                method: 'PATCH'
            });
            if (res.ok) {
                calendar.refetchEvents();
                loadEventDetail(currentSelectedEventId);
            }
        } catch (err) {
            alert('Gagal memperbarui status');
        }
    });

    // Delete Event Button Click -> Open Modal (UC-05)
    deleteEventBtn.addEventListener('click', () => {
        if (!currentSelectedEventId) return;
        deleteEventTitlePreview.textContent = `"${detailTitle.textContent}"`;
        deleteConfirmModal.classList.remove('hidden');
    });

    cancelDeleteBtn.addEventListener('click', () => {
        deleteConfirmModal.classList.add('hidden');
    });

    confirmDeleteBtn.addEventListener('click', async () => {
        if (!currentSelectedEventId) return;
        try {
            const res = await fetch(`/api/events/${currentSelectedEventId}`, {
                method: 'DELETE'
            });
            if (res.ok) {
                deleteConfirmModal.classList.add('hidden');
                currentSelectedEventId = null;
                detailContent.classList.add('hidden');
                detailEmpty.classList.remove('hidden');
                calendar.refetchEvents();
            } else {
                alert('Gagal menghapus event.');
            }
        } catch (err) {
            alert('Terjadi kesalahan jaringan.');
        }
    });

    // Edit Event Button Click -> Open Modal with data (UC-04)
    editEventBtn.addEventListener('click', async () => {
        if (!currentSelectedEventId) return;
        try {
            const res = await fetch(`/api/events/${currentSelectedEventId}`);
            if (!res.ok) return;
            const event = await res.json();
            openEventModalForEdit(event);
        } catch (err) {
            alert('Gagal mengambil data event');
        }
    });

    // ==========================================
    //  5. Modal Form Event (UC-03, UC-04, UC-09)
    // ==========================================

    function openEventModalForCreate(initialDate = null) {
        eventForm.reset();
        formEventId.value = '';
        modalTitle.textContent = 'Tambah Event Baru';
        titleError.classList.add('hidden');
        timeError.classList.add('hidden');

        // Set initial start date
        const start = initialDate ? new Date(initialDate) : new Date();
        if (!initialDate) {
            start.setHours(start.getHours() + 1, 0, 0, 0);
        } else {
            // Jika diklik dari grid bulan tanpa jam, set jam 09:00
            if (start.getHours() === 0 && start.getMinutes() === 0) {
                start.setHours(9, 0, 0, 0);
            }
        }
        eventStartInput.value = formatDateTimeLocal(start);

        const end = new Date(start);
        end.setHours(end.getHours() + 1);
        eventEndInput.value = formatDateTimeLocal(end);

        eventAllDayInput.checked = false;
        eventModal.classList.remove('hidden');
        eventTitleInput.focus();
    }

    function openEventModalForEdit(event) {
        eventForm.reset();
        formEventId.value = event.id;
        modalTitle.textContent = 'Ubah Event';
        titleError.classList.add('hidden');
        timeError.classList.add('hidden');

        eventTitleInput.value = event.title;
        eventAllDayInput.checked = event.all_day;
        eventStartInput.value = formatDateTimeLocal(event.start_at);
        eventEndInput.value = event.end_at ? formatDateTimeLocal(event.end_at) : '';
        eventCategorySelect.value = event.category_id || '';
        eventPrioritySelect.value = event.priority || 'sedang';
        eventLocationInput.value = event.location || '';
        eventDescriptionInput.value = event.description || '';

        // Uncheck all reminders first, then check matching
        document.querySelectorAll('input[name="reminderOffset"]').forEach(cb => {
            cb.checked = false;
        });

        if (event.reminders) {
            event.reminders.forEach(r => {
                const cb = document.querySelector(`input[name="reminderOffset"][value="${r.offset_minutes}"]`);
                if (cb) cb.checked = true;
            });
        }

        eventModal.classList.remove('hidden');
        eventTitleInput.focus();
    }

    openNewEventModalBtn.addEventListener('click', () => openEventModalForCreate());
    closeEventModalBtn.addEventListener('click', () => eventModal.classList.add('hidden'));
    cancelEventModalBtn.addEventListener('click', () => eventModal.classList.add('hidden'));

    // Handle allDay checkbox toggle
    eventAllDayInput.addEventListener('change', (e) => {
        const isAllDay = e.target.checked;
        if (isAllDay) {
            eventEndInput.parentElement.classList.add('opacity-50');
        } else {
            eventEndInput.parentElement.classList.remove('opacity-50');
        }
    });

    // Form Submit (Create / Update)
    eventForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        titleError.classList.add('hidden');
        timeError.classList.add('hidden');

        const title = eventTitleInput.value.trim();
        const startVal = eventStartInput.value;
        const endVal = eventEndInput.value;
        const isAllDay = eventAllDayInput.checked;
        const categoryId = eventCategorySelect.value ? parseInt(eventCategorySelect.value) : null;
        const priority = eventPrioritySelect.value;
        const location = eventLocationInput.value.trim();
        const description = eventDescriptionInput.value.trim();
        const id = formEventId.value;

        // Validasi input di browser
        if (!title) {
            titleError.textContent = 'Judul event wajib diisi.';
            titleError.classList.remove('hidden');
            return;
        }

        if (!startVal) {
            alert('Waktu mulai wajib diisi.');
            return;
        }

        if (!isAllDay && endVal) {
            if (new Date(endVal) < new Date(startVal)) {
                timeError.textContent = 'Waktu selesai tidak boleh lebih awal dari waktu mulai.';
                timeError.classList.remove('hidden');
                return;
            }
        }

        // Reminders offsets
        const reminders = [];
        document.querySelectorAll('input[name="reminderOffset"]:checked').forEach(cb => {
            reminders.push(parseInt(cb.value));
        });

        const payload = {
            title,
            start_at: new Date(startVal).toISOString(),
            end_at: (!isAllDay && endVal) ? new Date(endVal).toISOString() : null,
            all_day: isAllDay,
            category_id: categoryId,
            priority,
            location,
            description,
            reminders
        };

        const method = id ? 'PUT' : 'POST';
        const url = id ? `/api/events/${id}` : '/api/events';

        try {
            const res = await fetch(url, {
                method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (res.ok) {
                const saved = await res.json();
                eventModal.classList.add('hidden');
                calendar.refetchEvents();
                loadEventDetail(saved.id);
            } else {
                const data = await res.json();
                if (data.errors) {
                    if (data.errors.title) {
                        titleError.textContent = data.errors.title[0];
                        titleError.classList.remove('hidden');
                    }
                    if (data.errors.end_at) {
                        timeError.textContent = data.errors.end_at[0];
                        timeError.classList.remove('hidden');
                    }
                } else {
                    alert(data.message || 'Gagal menyimpan event');
                }
            }
        } catch (err) {
            alert('Terjadi kesalahan koneksi.');
        }
    });

    // ==========================================
    //  6. Filters & Search (UC-07, F-09)
    // ==========================================

    // Live Search with Debounce
    let searchTimeout;
    globalSearchInput.addEventListener('input', (e) => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            activeFilters.search = e.target.value.trim();
            calendar.refetchEvents();
        }, 300);
    });

    // Status Filter buttons
    statusFilterBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            statusFilterBtns.forEach(b => {
                b.className = 'filter-status-btn px-2.5 py-1 text-xs rounded-lg font-medium bg-slate-100 text-slate-600 hover:bg-slate-200';
            });
            btn.className = 'filter-status-btn active px-2.5 py-1 text-xs rounded-lg font-medium bg-indigo-600 text-white';
            activeFilters.status = btn.dataset.status;
            calendar.refetchEvents();
        });
    });

    // Priority Filter
    priorityFilterSelect.addEventListener('change', (e) => {
        activeFilters.priority = e.target.value;
        calendar.refetchEvents();
    });

    // Category Filter checkboxes
    categoryCheckboxes.forEach(cb => {
        cb.addEventListener('change', () => {
            if (cb.value === 'ALL') {
                if (cb.checked) {
                    categoryCheckboxes.forEach(c => {
                        if (c.value !== 'ALL') c.checked = false;
                    });
                    activeFilters.category = 'ALL';
                }
            } else {
                const allCb = document.querySelector('.category-checkbox[value="ALL"]');
                if (allCb) allCb.checked = false;

                // Cek yang terpilih
                const selected = Array.from(categoryCheckboxes)
                    .filter(c => c.checked && c.value !== 'ALL')
                    .map(c => c.value);

                if (selected.length === 0) {
                    if (allCb) allCb.checked = true;
                    activeFilters.category = 'ALL';
                } else if (selected.length === 1) {
                    activeFilters.category = selected[0];
                } else {
                    // Jika memilih lebih dari 1, untuk MVP filter satu atau re-query
                    activeFilters.category = selected[0];
                }
            }
            calendar.refetchEvents();
        });
    });

    // ==========================================
    //  7. Upcoming Events Summary (F-11)
    // ==========================================

    function updateUpcomingList(events) {
        upcomingEventsList.innerHTML = '';
        const now = new Date();

        const upcoming = events
            .filter(e => e.status !== 'selesai' && new Date(e.start_at) >= now)
            .sort((a, b) => new Date(a.start_at) - new Date(b.start_at))
            .slice(0, 5);

        upcomingBadge.textContent = upcoming.length;

        if (upcoming.length === 0) {
            upcomingEventsList.innerHTML = '<p class="text-slate-400 italic text-[11px]">Tidak ada agenda mendatang</p>';
            return;
        }

        upcoming.forEach(ev => {
            const item = document.createElement('div');
            item.className = 'p-2 rounded-lg bg-slate-50 border border-slate-100 hover:bg-slate-100 cursor-pointer transition flex items-center justify-between gap-2';
            item.innerHTML = `
                <div class="flex items-center gap-2 truncate">
                    <span class="w-2 h-2 rounded-full shrink-0" style="background-color: ${ev.category_color || '#4f46e5'}"></span>
                    <span class="font-medium text-slate-800 truncate">${ev.title}</span>
                </div>
                <span class="text-[10px] text-slate-400 shrink-0">${new Date(ev.start_at).toLocaleDateString('id-ID', { day: 'numeric', month: 'short' })}</span>
            `;
            item.addEventListener('click', () => loadEventDetail(ev.id));
            upcomingEventsList.appendChild(item);
        });
    }

    // Expose select event function to global scope for toast interactions
    window.selectCalendarEvent = function (id) {
        loadEventDetail(id);
    };
});
