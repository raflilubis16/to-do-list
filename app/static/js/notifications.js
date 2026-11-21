/**
 * Agenda - Notification & Polling Service
 * UC-10: Polling /api/reminders/due every 30 seconds
 * Displays Toast in-page and Desktop Notification via Notification API
 * UC-11: Snooze reminder support
 */

(function () {
    const POLLING_INTERVAL_MS = 30000; // 30 detik sesuai Bab 3.3 & Bab 5.2
    const toastContainer = document.getElementById('toastContainer');
    const shownReminderIds = new Set();

    // Minta izin notifikasi browser secara otomatis atau saat load jika default
    if ('Notification' in window && Notification.permission === 'default') {
        Notification.requestPermission().catch(() => {});
    }

    /**
     * Polling pengingat due dari server
     */
    async function checkDueReminders() {
        try {
            const res = await fetch('/api/reminders/due');
            if (!res.ok) return;
            const dueList = await res.json();

            if (Array.isArray(dueList) && dueList.length > 0) {
                dueList.forEach(reminder => {
                    // Hindari menampilkan toast ganda untuk id yang sama di sesi aktif
                    if (!shownReminderIds.has(reminder.id)) {
                        shownReminderIds.add(reminder.id);
                        showReminderToast(reminder);
                        showDesktopNotification(reminder);
                    }
                });
            }
        } catch (err) {
            console.warn('Gagal memeriksa pengingat due:', err);
        }
    }

    /**
     * Menampilkan Desktop Notification (Notification API)
     */
    function showDesktopNotification(reminder) {
        if (!('Notification' in window) || Notification.permission !== 'granted') return;

        const title = `Pengingat: ${reminder.event_title || 'Agenda'}`;
        let body = 'Waktu aktivitas telah tiba!';
        if (reminder.offset_minutes > 0) {
            body = `Aktivitas dimulai dalam ${reminder.offset_minutes} menit lagi.`;
        } else if (reminder.offset_minutes === 0) {
            body = 'Aktivitas Anda sedang dimulai sekarang.';
        }

        try {
            const n = new Notification(title, {
                body,
                icon: 'https://cdn-icons-png.flaticon.com/512/3652/3652191.png',
                tag: `reminder-${reminder.id}`
            });

            n.onclick = function () {
                window.focus();
                if (window.selectCalendarEvent && reminder.event_id) {
                    window.selectCalendarEvent(reminder.event_id);
                }
                ackReminder(reminder.id);
                n.close();
            };
        } catch (e) {
            console.error('Desktop notification error:', e);
        }
    }

    /**
     * Menampilkan Toast Notifikasi di Kanan Bawah Halaman (Bab 9.3)
     */
    function showReminderToast(reminder) {
        if (!toastContainer) return;

        const toast = document.createElement('div');
        toast.className = 'pointer-events-auto bg-slate-800 text-white rounded-xl shadow-xl p-4 border border-slate-700 flex flex-col gap-2.5 animate-slide-up';
        toast.dataset.id = reminder.id;

        let timeMsg = 'Waktunya telah tiba!';
        if (reminder.offset_minutes > 0) {
            timeMsg = `dimulai ${reminder.offset_minutes} menit lagi`;
        } else if (reminder.offset_minutes === 0) {
            timeMsg = 'dimulai sekarang';
        }

        toast.innerHTML = `
            <div class="flex items-start justify-between gap-3">
                <div class="flex items-start gap-2.5">
                    <div class="w-7 h-7 rounded-lg bg-indigo-500/20 text-indigo-400 flex items-center justify-center shrink-0 mt-0.5">
                        <i class="fa-solid fa-bell text-xs"></i>
                    </div>
                    <div>
                        <h4 class="text-xs font-semibold text-white leading-tight">Pengingat: ${escapeHTML(reminder.event_title || 'Agenda')}</h4>
                        <p class="text-[11px] text-slate-300 mt-0.5">${timeMsg}</p>
                    </div>
                </div>
                <button type="button" class="toast-close-btn text-slate-400 hover:text-white p-1 rounded" title="Tutup">
                    <i class="fa-solid fa-xmark text-xs"></i>
                </button>
            </div>
            <div class="flex items-center justify-end gap-2 pt-1 border-t border-slate-700/60">
                <button type="button" class="toast-view-btn text-[11px] text-indigo-400 hover:text-indigo-300 font-medium px-2 py-1 rounded">
                    Lihat detail
                </button>
                <button type="button" class="toast-snooze-btn text-[11px] text-amber-400 hover:text-amber-300 font-medium px-2 py-1 rounded">
                    Tunda 10 menit
                </button>
                <button type="button" class="toast-ack-btn text-[11px] bg-slate-700 hover:bg-slate-600 text-white font-medium px-2.5 py-1 rounded transition">
                    Tutup
                </button>
            </div>
        `;

        // Event listeners untuk toast
        const closeBtn = toast.querySelector('.toast-close-btn');
        const ackBtn = toast.querySelector('.toast-ack-btn');
        const snoozeBtn = toast.querySelector('.toast-snooze-btn');
        const viewBtn = toast.querySelector('.toast-view-btn');

        const dismiss = () => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateY(10px)';
            toast.style.transition = 'all 0.2s ease';
            setTimeout(() => toast.remove(), 200);
        };

        // Close / Ack (UC-10)
        const handleAck = async () => {
            await ackReminder(reminder.id);
            dismiss();
        };

        closeBtn.addEventListener('click', handleAck);
        ackBtn.addEventListener('click', handleAck);

        // Snooze (UC-11)
        snoozeBtn.addEventListener('click', async () => {
            try {
                await fetch(`/api/reminders/${reminder.id}/snooze`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ minutes: 10 })
                });
                dismiss();
            } catch (err) {
                console.error(err);
            }
        });

        // View detail
        viewBtn.addEventListener('click', () => {
            if (window.selectCalendarEvent && reminder.event_id) {
                window.selectCalendarEvent(reminder.event_id);
            }
            handleAck();
        });

        toastContainer.appendChild(toast);
    }

    /**
     * Memanggil /api/reminders/{id}/ack (status -> delivered)
     */
    async function ackReminder(reminderId) {
        try {
            await fetch(`/api/reminders/${reminderId}/ack`, { method: 'POST' });
        } catch (e) {
            console.warn('Ack failed', e);
        }
    }

    function escapeHTML(str) {
        if (!str) return '';
        const d = document.createElement('div');
        d.textContent = str;
        return d.innerHTML;
    }

    // Expose showReminderToast for testing
    window.showReminderToast = showReminderToast;

    // Mulai polling saat halaman selesai dimuat
    document.addEventListener('DOMContentLoaded', () => {
        // Cek langsung saat buka halaman (T-06)
        checkDueReminders();
        // Polling setiap 30 detik
        setInterval(checkDueReminders, POLLING_INTERVAL_MS);
    });
})();
