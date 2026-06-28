/** Strip dangerous HTML before {@html} rendering (backend also sanitizes). */
export function sanitizeHtml(html: string | null | undefined): string {
	if (!html) return '';
	if (typeof DOMParser !== 'undefined') {
		const doc = new DOMParser().parseFromString(html, 'text/html');
		doc.querySelectorAll('script, style, iframe, object, embed').forEach((el) => el.remove());
		doc.querySelectorAll('*').forEach((el) => {
			for (const attr of [...el.attributes]) {
				if (attr.name.startsWith('on') || attr.value.trim().toLowerCase().startsWith('javascript:')) {
					el.removeAttribute(attr.name);
				}
			}
		});
		return doc.body.innerHTML;
	}
	return html
		.replace(/<script[\s\S]*?<\/script>/gi, '')
		.replace(/<iframe[\s\S]*?<\/iframe>/gi, '')
		.replace(/\son\w+="[^"]*"/gi, '');
}
