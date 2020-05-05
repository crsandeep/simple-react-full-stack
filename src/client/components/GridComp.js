import React from 'react';
import RGL, { WidthProvider } from 'react-grid-layout';
import '../css/react-grid-layout-styles.css';
import '../css/react-resizable-styles.css';
import '../css/SpaceGrid.css';
import PropTypes from 'prop-types';

import {
  Row, Col, ButtonToolbar, Spinner, Alert, Badge
} from 'react-bootstrap';

import { IconButton } from '@material-ui/core/';
import AddCircleOutlineIcon from '@material-ui/icons/AddCircleOutline';
import PlaylistAddIcon from '@material-ui/icons/PlaylistAdd';
import SaveIcon from '@material-ui/icons/Save';
import DeleteIcon from '@material-ui/icons/Delete';
import HighlightOffIcon from '@material-ui/icons/HighlightOff';

import { Prompt } from 'react-router';

const ReactGridLayout = WidthProvider(RGL);

function GridComp(props) {
  const [mode, setMode] = React.useState('edit');

  return (
    <div>
      <Prompt when={props.isDirtyWrite} message="Changes you made may not be saved. Are you sure you want to leave?" />
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
                      style={props.gridImgPath != null ? { backgroundImage: `url(${props.gridImgPath})` } : ''}
                    >
                      {
                        parseInt(grid.i, 10) > 0 ? (
                          <h3 className="spaceGrid-idPanel">{grid.i.padStart(2, '0')}</h3>
                        ) : (
                          <h3 className="spaceGrid-newIdPanel">{`New ${(Math.abs(grid.i) - 1).toString().padStart(2, '0')}`}</h3>
                        )
                      }

                      {
                        props.tagsMap != null
                        && props.tagsMap.get(grid.i) != null
                        && props.tagsMap.get(grid.i).map((tag, i) => (
                          // console.log(`Val: ${tag}`)
                          <span key={`${grid.i}-${tag}`}>
                            <Badge variant="warning">
                              #
                              {tag}
                            </Badge>
                            {' '}
                          </span>
                        ))
                      }
                      <ButtonToolbar className="spaceGrid-btn">
                        {parseInt(grid.i, 10) > 0
                          ? (
                            <IconButton
                              aria-label="select"
                              onClick={() => props.handleSelect(grid.i)}
                            >
                              <PlaylistAddIcon />
                            </IconButton>
                          )
                          : null
                        }

                        {
                          parseInt(grid.i, 10) < 0
                        || (props.tagsMap != null
                        && props.tagsMap.get(grid.i) != null
                        && props.tagsMap.get(grid.i).length === 0
                        ) ? (
                          <IconButton
                            aria-label="delete"
                            onClick={() => props.handleRemove(grid.i)}
                          >
                            <DeleteIcon />
                          </IconButton>
                            ) : null
                        }

                      </ButtonToolbar>
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

GridComp.defaultProps = {
  gridImgPath: null
};

GridComp.propTypes = {
  formState: PropTypes.oneOfType([PropTypes.object]).isRequired,
  tempLayouts: PropTypes.arrayOf(PropTypes.object).isRequired,
  tagsMap: PropTypes.oneOfType([PropTypes.object]).isRequired,
  isDirtyWrite: PropTypes.bool.isRequired,
  gridImgPath: PropTypes.string,
  handleNew: PropTypes.func.isRequired,
  handleToggleMode: PropTypes.func.isRequired,
  handleSave: PropTypes.func.isRequired,
  handleCancel: PropTypes.func.isRequired,
  handleUpdateLayout: PropTypes.func.isRequired,
  handleRemove: PropTypes.func.isRequired,
  handleSelect: PropTypes.func.isRequired
};

export default GridComp;
