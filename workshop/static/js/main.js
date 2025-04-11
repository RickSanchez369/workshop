// ⭐ فرمت هزارگان برای قیمت (input.text + hidden input)
document.addEventListener('DOMContentLoaded', function () {
    const formattedInputs = document.querySelectorAll('.formatted-amount');

    formattedInputs.forEach(function (visibleInput) {
        const form = visibleInput.closest('form');
        const hiddenInput = form.querySelector('.raw-amount');

        if (!hiddenInput) return;

        visibleInput.addEventListener('input', function () {
            let raw = visibleInput.value.replace(/,/g, '').replace(/[^\d]/g, '');
            if (raw) {
                visibleInput.value = Number(raw).toLocaleString('en-US');
                hiddenInput.value = raw;
            } else {
                hiddenInput.value = '';
            }
        });

        form.addEventListener('submit', function () {
            let raw = visibleInput.value.replace(/,/g, '').replace(/[^\d]/g, '');
            hiddenInput.value = raw;
        });
    });
});

// ✅ فعال‌سازی Persian Datepicker برای input‌های visible
$(document).ready(function () {
    $('.datepicker').each(function () {
        if (!$(this).data('datepicker')) {
            $(this).persianDatepicker({
                format: 'YYYY/MM/DD',
                initialValueType: 'gregorian',
                calendarType: 'persian',
                autoClose: true,
                toolbox: {
                    calendarSwitch: {
                        enabled: false
                    }
                }
            });
        }
    });

    // 🔄 فعال‌سازی دوباره برای فیلدهایی که داخل modal هستن
    $('.modal').on('shown.bs.modal', function () {
        $(this).find('.datepicker').each(function () {
            if (!$(this).data('datepicker')) {
                $(this).persianDatepicker({
                    format: 'YYYY/MM/DD',
                    initialValueType: 'gregorian',
                    calendarType: 'persian',
                    autoClose: true,
                    toolbox: {
                        calendarSwitch: {
                            enabled: false
                        }
                    }
                });
            }
        });
    });
});
