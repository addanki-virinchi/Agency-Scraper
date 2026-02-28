# Google Maps Smooth Scroll-to-Zoom Implementation

This project demonstrates a smooth scroll-to-zoom functionality for Google Maps using the Google Maps JavaScript API. The map responds to mouse wheel and trackpad gestures to zoom in and out when the user's cursor is hovering over it, without interfering with the main page's vertical scroll.

## Features

- **Smooth Zoom Animation**: Gradual zoom transitions for a better user experience
- **Mouse Wheel Support**: Zoom in/out using the mouse wheel when hovering over the map
- **Trackpad Gesture Support**: Responds to trackpad pinch gestures
- **Context-Aware**: Zoom only works when the cursor is over the map
- **Non-Intrusive**: Doesn't interfere with the main page's vertical scrolling
- **Visual Feedback**: Shows current zoom level when hovering over the map

## How to Use

1. **Get a Google Maps API Key**:
   - Go to the [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one
   - Enable the "Maps JavaScript API" for your project
   - Create credentials (API Key)
   - Restrict your API key for security (recommended)

2. **Configure the API Key**:
   - Open `google-maps-scroll-zoom.html`
   - Replace `YOUR_API_KEY` in line 185 with your actual Google Maps API key:
   ```html
   <script async defer
       src="https://maps.googleapis.com/maps/api/js?key=YOUR_ACTUAL_API_KEY&callback=initMap">
   </script>
   ```

3. **Open the HTML File**:
   - Open `google-maps-scroll-zoom.html` in a web browser
   - The map will load centered on New Delhi with some sample markers

## How It Works

### Mouse Wheel Detection
The implementation listens for `wheel` events on the map element and prevents the default scroll behavior when the cursor is over the map.

### Smooth Zoom Animation
Instead of instantly changing the zoom level, the implementation uses a step-by-step animation that gradually adjusts the zoom level, creating a smooth visual effect.

### Context Awareness
The system tracks whether the mouse is over the map using `mouseenter` and `mouseleave` events, ensuring that zoom only occurs when appropriate.

### Trackpad Support
The implementation includes gesture event handlers for trackpad pinch-to-zoom functionality.

## Customization

### Changing the Default Location
To change the default map center, modify the `defaultLocation` object in the `initMap()` function:
```javascript
const defaultLocation = { lat: LATITUDE, lng: LONGITUDE };
```

### Adjusting Zoom Speed
To change the zoom animation speed, modify the timeout value in the `animateZoom()` function:
```javascript
smoothZoomAnimation = setTimeout(animateZoom, 50); // Increase for slower zoom
```

### Changing Zoom Limits
To adjust the minimum and maximum zoom levels, modify the `smoothZoomTo()` function:
```javascript
const newZoom = Math.max(MIN_ZOOM, Math.max(MAX_ZOOM, currentZoom + zoomDirection));
```

## Browser Compatibility

This implementation works in all modern browsers that support:
- Google Maps JavaScript API
- Wheel events
- Gesture events (for trackpad support)

## Security Considerations

- Always restrict your Google Maps API key to specific domains
- Consider implementing server-side API key proxy for production environments
- Monitor your API usage to prevent unexpected charges

## Troubleshooting

### Map Not Loading
- Verify your API key is correct and properly configured
- Check that the Maps JavaScript API is enabled in your Google Cloud Console
- Ensure your browser has JavaScript enabled

### Scroll Not Working
- Make sure your cursor is directly over the map area
- Check that no other elements are overlaying the map
- Verify that the map has focus (try clicking on it first)

### Zoom Not Smooth
- Check browser performance - older browsers may have animation issues
- Try reducing the number of markers on the map
- Consider adjusting the animation timeout values

## License

This implementation is provided as an example. Please ensure you comply with Google Maps Platform Terms of Service when using this code in production.