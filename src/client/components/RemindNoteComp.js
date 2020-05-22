import React from 'react';
import moment from 'moment';
import PropTypes from 'prop-types';
import AccessAlarmIcon from '@material-ui/icons/AccessAlarm';
import AlarmOffIcon from '@material-ui/icons/AlarmOff';
import { IconButton } from '@material-ui/core';

const calRemindDisplayTxt = (remindDtm) => {
  if (remindDtm != null) {
    let remindDayStr = null;
    const currMoment = moment(new Date()).startOf('day'); // set as 00:00

    const remindMoment = moment(remindDtm);

    // calculate for is today or yesterday
    const hourDiff = remindMoment.diff(moment(currMoment), 'seconds', true);
    if (hourDiff < 86400 && hourDiff >= 0) {
      remindDayStr = 'Today';
    } else if (hourDiff < 0 && hourDiff >= -86400) {
      remindDayStr = 'Yesterday';
    } else {
      remindDayStr = remindMoment.format('D MMM, YYYY');
    }
    remindDayStr += remindMoment.format(' hh:mm A');

    // calculate is the alarm passed, display diff alarm icon
    const secDiff = remindMoment.diff(moment(new Date()), 'seconds', true);
    return (
      <span>
        {
          secDiff > -60
            ? <AccessAlarmIcon />
            : <AlarmOffIcon />
        }
        {
            secDiff > -60
              ? <small>{remindDayStr}</small>
              : <small className="text-muted">{remindDayStr}</small>
        }
      </span>
    );
  }
  return null;
};

function RemindNoteComp(props) {
  return calRemindDisplayTxt(props.remindDtm);
}

RemindNoteComp.defaultProps = {
  remindDtm: null
};

RemindNoteComp.propTypes = {
  remindDtm: PropTypes.string
};

export default RemindNoteComp;
