import './App.css';
import React, { useState } from 'react';

import DateTimeRangePicker from '@wojtekmaj/react-datetimerange-picker'; // Date Selection for photolist
import { ApolloProvider, ApolloClient, InMemoryCache, gql, useQuery } from '@apollo/client'; // Graphql client
import Masonry, { ResponsiveMasonry } from "react-responsive-masonry" // Layout for the photolist
import LazyLoad from 'react-lazyload'; // Lazy loading for photos in the photolist
import { Map, Marker } from "pigeon-maps" // Photo Mini map
import ReactJson from 'react-json-view' // Exif data display

// Get list of all photos between two dates
const PHOTOLIST = gql`query getPhotolist($startdatetime: DateTime!, $enddatetime: DateTime!) {
  photolist(startdatetime: $startdatetime, enddatetime: $enddatetime)
}`;

// Get photo contents from a filename key
const PHOTO = gql`query getPhoto($filename: String!) {
  photo(filename: $filename) {
    filetype
    filename
    datetaken
    latitude
    longitude
    thumbnail
    exifdata
  }
}`;

function MiniMap({latitude, longitude}) {
  const [isShown, setIsShown] = useState(false);

  return (
    <div>
      <p onClick={() => setIsShown(!isShown)}>
        Location = {latitude},{longitude} (click to show/hide map)
      </p>
      {isShown && (
        <Map height={512} width={512} defaultCenter={[latitude,longitude]} defaultZoom={10} zoom={false} >
          <Marker width={20} anchor={[latitude,longitude]} />
        </Map>
      )}
    </div>
  )
}

function ExifData({exifdata}) {
  const [isShown, setIsShown] = useState(false);

  return (
    <div>
      <p onClick={() => setIsShown(!isShown)}>
        Exif = (click to show/hide)
      </p>
      {isShown && (<ReactJson src={JSON.parse(exifdata)} />)}
    </div>
  )
}


// Render a Photo based on the graphql call, input is filename/key.
function Photo({filename}) {
  const {loading, error, data} = useQuery(PHOTO, { variables: {filename} });

  if (loading) return <img alt='loading...' src='loading.gif'/>;
  if (error) return <img alt='error' src='error.gif'/>;

  const thumbnail = "data:image/jpeg;base64, "+ data.photo.thumbnail;

  return (
    <div id='photo'>
      <img alt={data.photo.filename} src={thumbnail}></img>
      <p>Filename = {data.photo.filename}</p>
      <p>Date Taken = {data.photo.datetaken}</p>
      <MiniMap latitude={data.photo.latitude} longitude={data.photo.longitude} />
      <ExifData exifdata={data.photo.exifdata} />
    </div> 
  )
}

// Render the full list of photos between a start and end date, calling graphql. 
// Using masonry for layout and lazyload to prevent loading of offscreen elements.
function PhotoList({startdatetime, enddatetime}) {
  const {loading, error, data} = useQuery(PHOTOLIST, {variables: { startdatetime: startdatetime, enddatetime: enddatetime}});

  if (loading) return <p>Loading...</p>;
  if (error) return <p>Error</p>;
  if (data.photolist.length === 0) return <p>No photos found</p>;

  return (
    <ResponsiveMasonry columnsCountBreakPoints={{522: 1, 1064: 2, 1596: 3}} >
      <Masonry>
        {data.photolist.map(filename => { return <LazyLoad height='512px'><Photo key={filename} filename={filename} /></LazyLoad>})}
      </Masonry>
    </ResponsiveMasonry>
  )
}

// Graphql client, enable in memory caching to save repeat requests. 
//Disable cors since we're using localhost.
const client = new ApolloClient({
  uri: 'http://127.0.0.1:5000/graphql',
  cache: new InMemoryCache(),
  fetchOptions: {
    mode: 'no-cors',
  }
});


// Our main app. An Apolo App that will load a set of photos based on the dates picked.
function App() {
  const [value, onChange] = useState([new Date(), new Date()]);

  return (
      <ApolloProvider client={client}>
          <div>
            <DateTimeRangePicker onChange={onChange} value={value} />
          </div>
          <PhotoList startdatetime={value[0]} enddatetime={value[1]} />
      </ApolloProvider>
    );
}

export default App;
