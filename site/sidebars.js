/**
 * Docusaurus sidebar configuration.
 */
module.exports = {
  tutorialSidebar: [
    {
      type: 'category',
      label: 'System Design',
      items: ['intro'],
    },
    {
      type: 'category',
      label: 'Operations',
      items: [
          'ops/SECRETS',
          'ops/SSRF',
      ],
    },
    {
        type: 'category',
        label: 'Security',
        items: ['security/policy'],
    }
  ],
};