import React from 'react';
import { makeStyles } from '@material-ui/core/styles';
import InputLabel from '@material-ui/core/InputLabel';
import FormHelperText from '@material-ui/core/FormHelperText';
import FormControl from '@material-ui/core/FormControl';
import Select from '@material-ui/core/Select';
import NativeSelect from '@material-ui/core/NativeSelect';

const useStyles = makeStyles(theme => ({
  formControl: {
    margin: theme.spacing(1),
    minWidth: 120,
  },
  selectEmpty: {
    marginTop: theme.spacing(2),
  },
}));

export default function NoteSelector() {
  const classes = useStyles();
  const [state, setState] = React.useState({
    note: '',
    name: 'hai',
  });

  const inputLabel = React.useRef(null);
  const [labelWidth, setLabelWidth] = React.useState(0);


  const handleChange = name => event => {
    setState({
      ...state,
      [name]: event.target.value,
    });
  };

  return (
    <div>
      <FormControl className={classes.formControl}>
        <InputLabel htmlFor="note-native-simple">Note</InputLabel>
        <Select
          native
          value={state.note}
          onChange={handleChange('note')}
          inputProps={{
            name: 'note',
            id: 'note-native-simple',
          }}
        >
          <option value="" />
          <option value={'C'}>C</option>
          <option value={'C#'}>C#</option>
          <option value={'D'}>D</option>
          <option value={'D#'}>D#</option>
          <option value={'E'}>E</option>
          <option value={'F'}>F</option>
          <option value={'F#'}>F#</option>
          <option value={'G'}>G</option>
          <option value={'G#'}>G#</option>
          <option value={'A'}>A</option>
          <option value={'A#'}>A#</option>
          <option value={'B'}>B</option>
        </Select>
      </FormControl>
    </div>
  );
}
