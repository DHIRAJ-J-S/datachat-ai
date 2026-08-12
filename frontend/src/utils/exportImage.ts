import html2canvas from 'html2canvas';

export const downloadElementAsImage = async (elementId: string, filename: string) => {
  const element = document.getElementById(elementId);
  if (!element) {
    console.error(`Element with id ${elementId} not found`);
    return;
  }

  try {
    const canvas = await html2canvas(element, {
      backgroundColor: '#1e1e2d', // Match the app's dark background
      scale: 2, // Higher resolution
      useCORS: true
    });
    
    const dataUrl = canvas.toDataURL('image/png');
    const link = document.createElement('a');
    link.download = `${filename}.png`;
    link.href = dataUrl;
    link.click();
  } catch (error) {
    console.error('Error generating image:', error);
  }
};
