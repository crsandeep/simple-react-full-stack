import React from 'react';
import { makeStyles } from '@material-ui/core/styles';
import Typography from '@material-ui/core/Typography';
import Slider from '@material-ui/core/Slider';

const useStyles = makeStyles(theme => ({
  root: {
    width: 500,
  },
  margin: {
    height: theme.spacing(3),
  },
}));

const marks = [
  {
    value: 0,
    label: '0°C',
  },
  {
    value: 20,
    label: '20°C',
  },
  {
    value: 37,
    label: '37°C',
  },
  {
    value: 100,
    label: '100°C',
  },
];

function valuetext(value) {
  return `${value}°C`;
}

function valueLabelFormat(value) {
  return marks.findIndex(mark => mark.value === value) + 1;
}

function changeHandler(){
  alert('');
}

export default function DiscreteSlider(props) {
  const classes = useStyles();

  return (
    <div className={classes.root}>
      <Slider
        value = {props.value}
        defaultValue={5}
        getAriaValueText={valuetext}
        aria-labelledby="discrete-slider"
        valueLabelDisplay="auto"
        onChangeCommitted={props.onChangeCommitted()}
        step={2}
        marks
        min={0}
        max={10}
      />
      </div>
  );
}
