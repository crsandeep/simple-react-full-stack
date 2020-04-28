import React from 'react';
import RGL, { WidthProvider } from 'react-grid-layout';
import '../css/react-grid-layout-styles.css';
import '../css/react-resizable-styles.css';
import '../css/SpaceGrid.css';
import PropTypes from 'prop-types';

import {
  Row, Col, ButtonToolbar, Spinner, Alert, Tooltip, OverlayTrigger
} from 'react-bootstrap';
import { IconButton } from '@material-ui/core/';
import AddCircleOutlineIcon from '@material-ui/icons/AddCircleOutline';
import PlaylistAddIcon from '@material-ui/icons/PlaylistAdd';
import SaveIcon from '@material-ui/icons/Save';
import DeleteIcon from '@material-ui/icons/Delete';
import HighlightOffIcon from '@material-ui/icons/HighlightOff';

const ReactGridLayout = WidthProvider(RGL);

function SpaceGrid(props) {
  const [mode, setMode] = React.useState('edit');
  return (
    <div>
      {
        // page loading mask
        props.formState.pageLoading === true && (
          <div className="overlay">
            <Spinner
              animation="border"
              role="status"
              size="lg"
              style={{ width: `${10}rem`, height: `${10}rem` }}
              className="mt-5"
            >
              <span className="sr-only">Loading...</span>
            </Spinner>
            <h5>Loading...</h5>
          </div>
        )
      }
      {props.tempLayouts != null && props.tempLayouts.length > 0 ? (
        <div>
          <Row>
            <Col xs={12} md={12}>
              {props.tempLayouts != null && props.tempLayouts.length === 1 && (parseInt(props.tempLayouts[0].i, 10) < 0) && (
                <Alert variant="success">
                  Ready to manage your space!
                  {' '}
                  Click
                  {' '}
                  <AddCircleOutlineIcon />
                  {' '}
                  to add a new grid.
                </Alert>
              )}
            </Col>

          </Row>
          <Row className="justify-content-md-center">
            <Col xs={12} md={6}>
              <ButtonToolbar>
                <IconButton aria-label="New" onClick={props.handleNew}>
                  <AddCircleOutlineIcon />
                </IconButton>
                <IconButton aria-label="Save" onClick={props.handleSave}>
                  <SaveIcon />
                </IconButton>
                <IconButton aria-label="Cancel" onClick={props.handleCancel}>
                  <HighlightOffIcon />
                </IconButton>
              </ButtonToolbar>
            </Col>
            <Col xs={12} md={6}>
              <div>
                Current Mode:
                <select
                  value={mode}
                  onChange={(event) => {
                    setMode(event.target.value);
                    props.handleToggleMode(mode === 'edit');
                  }}
                >
                  <option value="edit">Edit</option>
                  <option value="view">View</option>
                </select>
              </div>
            </Col>
          </Row>
          <Row>
            <Col xs={12} md={12}>
              <ReactGridLayout
                cols={12}
                rowHeight={120}
                layout={props.tempLayouts}
                onLayoutChange={props.handleUpdateLayout}
              >
                {props.tempLayouts !== null
                  && props.tempLayouts.map(grid => (
                    <div
                      key={grid.i}
                      className={
                        grid.static ? 'spaceGrid-grid-static' : 'spaceGrid-grid'
                      }
                    >
                      <OverlayTrigger
                        overlay={<Tooltip>Drag to move your grid position</Tooltip>}
                        placement="right"
                      >
                        <div>
                          <h1>{grid.i}</h1>
                          <ButtonToolbar className="spaceGrid-btn">
                            <IconButton
                              aria-label="select"
                              onClick={() => props.handleSelect(grid.i)}
                            >
                              <PlaylistAddIcon />
                            </IconButton>
                            <IconButton
                              aria-label="delete"
                              onClick={() => props.handleRemove(grid.i)}
                            >
                              <DeleteIcon />
                            </IconButton>
                          </ButtonToolbar>
                        </div>
                      </OverlayTrigger>
                    </div>
                  ))
                }

              </ReactGridLayout>
            </Col>
          </Row>
        </div>
      ) : (
        <Alert variant="info">
          Please select your space from left side menu!
        </Alert>
      )}
    </div>
  );
}

SpaceGrid.propTypes = {
  formState: PropTypes.oneOfType([PropTypes.object]).isRequired,
  tempLayouts: PropTypes.arrayOf(PropTypes.object),
  handleNew: PropTypes.func.isRequired,
  handleToggleMode: PropTypes.func.isRequired,
  handleSave: PropTypes.func.isRequired,
  handleCancel: PropTypes.func.isRequired,
  handleUpdateLayout: PropTypes.func.isRequired,
  handleRemove: PropTypes.func.isRequired,
  handleSelect: PropTypes.func.isRequired
};

export default SpaceGrid;
