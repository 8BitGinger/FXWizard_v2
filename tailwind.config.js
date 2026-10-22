// Tailwind settings for css/tailwind.css (the layout classes in fx_wizard.html, like "grid grid-cols-2 gap-1").
// After adding or changing classes in fx_wizard.html, rebuild it:   npm run build:css
// (It used to be built in the browser from cdn.tailwindcss.com every time the page opened, which needed the
// internet and slowed opening. Same Tailwind version as that CDN: 3.4.17.)
module.exports = {
    content: ['./fx_wizard.html'],
    theme: {
        extend: {
            // Color names used in the page (bg-primary etc.)
            colors: {
                'primary': '#6D28D9',
                'secondary': '#C4A127',
                'bg-dark': '#333333',
            },
        },
    },
};
