import React from 'react';
import { makeStyles } from '@material-ui/core/styles';
import InputLabel from '@material-ui/core/InputLabel';
import MenuItem from '@material-ui/core/MenuItem';
import FormHelperText from '@material-ui/core/FormHelperText';
import FormControl from '@material-ui/core/FormControl';
import Select from '@material-ui/core/Select';

const useStyles = makeStyles(theme => ({
  formControl: {
    margin: theme.spacing(1),
    minWidth: 120,
  },
  selectEmpty: {
    marginTop: theme.spacing(2),
  },
}));

export default function NoteSelector(props) {
  const classes = useStyles();
  const [note, setNote] = React.useState('');

  const inputLabel = React.useRef(null);
  const [labelWidth, setLabelWidth] = React.useState(0);

  const handleChange = event => {
    setNote(event.target.value);
  };

  return (
    <div>
      <FormControl className={classes.formControl}>
        <InputLabel id="demo-simple-select-label">Note</InputLabel>
        <Select
          labelId="demo-simple-select-label"
          id="demo-simple-select"
          value={props.value}
          onChange={props.onChange()}
        >
          <MenuItem value={'C'}>C</MenuItem>
          <MenuItem value={'C#'}>C#</MenuItem>
          <MenuItem value={'D'}>D</MenuItem>
          <MenuItem value={'D#'}>D#</MenuItem>
          <MenuItem value={'E'}>E</MenuItem>
          <MenuItem value={'F'}>F</MenuItem>
          <MenuItem value={'F#'}>F#</MenuItem>
          <MenuItem value={'G'}>G</MenuItem>
          <MenuItem value={'G#'}>G#</MenuItem>
          <MenuItem value={'A'}>A</MenuItem>
          <MenuItem value={'A#'}>A#</MenuItem>
          <MenuItem value={'B'}>B</MenuItem>
        </Select>
      </FormControl>
      </div>
    )
  }
