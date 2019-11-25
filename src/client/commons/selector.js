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

export default function NativeSelects() {
  const classes = useStyles();
  const [state, setState] = React.useState({
    instrument: '',
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
        <InputLabel htmlFor="instrument-native-simple">Instrument</InputLabel>
        <Select
          native
          value={state.instrument}
          onChange={handleChange('instrument')}
          inputProps={{
            name: 'instrument',
            id: 'instrument-native-simple',
          }}
        >
          <option value="" />
          <option value={'Synth1'}>Synth1</option>
          <option value={'Synth2'}>Synth2</option>
          <option value={'Piano'}>Piano</option>
          <option value={'Water'}>Water</option>
        </Select>
      </FormControl>
    </div>
  );
}
