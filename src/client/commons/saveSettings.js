import React from 'react';
import Button from '@material-ui/core/Button';
import { makeStyles } from '@material-ui/core/styles';
import Icon from '@material-ui/core/Icon';

const useStyles = makeStyles(theme => ({
  button: {
    margin: theme.spacing(1),
  },
}));

export default function SaveSettings(props) {
  const classes = useStyles();

  return (
    <div>
    <Button
      variant="contained"
      color="primary"
      size="small"
      className={classes.button}
    >
      Save
    </Button>
    </div>
  );
}
