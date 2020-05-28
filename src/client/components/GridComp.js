import React from 'react';
import RGL, { WidthProvider } from 'react-grid-layout';
import PropTypes from 'prop-types';
import {
  Row, Col, ButtonToolbar, Alert, Badge, OverlayTrigger, Tooltip
} from 'react-bootstrap';
import {
  IconButton, FormControlLabel, Switch, Box, Divider, Button
} from '@material-ui/core/';
import {
  FormatListBulleted, PostAdd, Delete,
  Cached, Add, ArrowBackIos, Check, ControlCameraOutlined
} from '@material-ui/icons';

import { Prompt } from 'react-router';
import * as Constants from '../constants/Grid';
import * as UIConstants from '../constants/Global';
import BaseUIComp from './BaseUIComp';

// css
import '../css/react-grid-layout-styles.css';
import '../css/react-resizable-styles.css';
import '../css/SpaceGrid.css';

const ReactGridLayout = WidthProvider(RGL);

function GridComp(props) {
  const isLargeScreen = (window.innerWidth > UIConstants.UI_SMALL_SCREEN_WIDTH);

  const renderTagsTooltip = (prop, text) => (
    <Tooltip id="button-tooltip" {...prop}>
      {text}
    </Tooltip>
  );

  // hook for switch view
  const [state, setState] = React.useState({
    isEditMode: false
  });
  const handleChange = (event) => {
    setState({ ...state, [event.target.name]: event.target.checked });
    props.handleToggleMode(event.target.checked ? Constants.FORM_EDIT_MODE : Constants.FORM_READONLY_MODE);
  };


  return (
    <div>
      <Prompt when={props.isDirtyWrite} message="Changes you made may not be saved. Are you sure you want to leave?" />

      <BaseUIComp
        displayMsg={props.displayMsg}
        pageLoading={props.pageLoading}
      />

      <Row>
        <Col xs={2} md={2}>
          <Box display="flex" justifyContent="flex-start">
            <IconButton
              aria-label="back"
              onClick={() => props.handleGoBack()}
            >
              <ArrowBackIos />
            </IconButton>
          </Box>
        </Col>
        <Col xs={10} md={10}>
          <Box display="flex" justifyContent="flex-end">
            <FormControlLabel
              control={(
                <Switch
                  checked={state.isListView}
                  onChange={handleChange}
                  name="isEditMode"
                  color="primary"
                  size="small"
                />
                )}
              label="Unlock"
              style={{ marginTop: '10px' }}
            />

            <IconButton aria-label="New" onClick={props.handleNew}>
              <Add />
            </IconButton>
            <IconButton aria-label="Save" onClick={props.handleSave}>
              <Check />
            </IconButton>
            <IconButton aria-label="Cancel" onClick={props.handleCancel}>
              <Cached />
            </IconButton>
          </Box>
        </Col>
      </Row>
      <Divider />
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
                  <Add />
                  {' '}
                  to add a new grid.
                </Alert>
              )}
            </Col>
          </Row>
          <Row>
            <Col xs={12} md={12}>
              <ReactGridLayout
                cols={4}
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
                        // generate ID panel
                        parseInt(grid.i, 10) > 0 ? (
                          <h3 className="spaceGrid-idPanel">{grid.i.padStart(2, '0').slice(-3)}</h3>
                        ) : (
                          <h3 className="spaceGrid-newIdPanel">{`New ${(Math.abs(grid.i) - 1).toString().padStart(2, '0')}`}</h3>
                        )
                      }

                      {
                        // edit mode - drag item message
                        props.currMode === Constants.FORM_EDIT_MODE // under edit mode
                        && (
                          <Box textAlign="center" fontSize="h6.fontSize" m={1} color="primary.main">
                            <ControlCameraOutlined />
                            Drag & Move
                          </Box>
                        )
                      }


                      {
                        // show go to item button only if read only mode
                        // and old grid
                          props.currMode === Constants.FORM_READONLY_MODE // under readonly mode
                          && parseInt(grid.i, 10) > 0 // old grid
                            && (
                              <Box textAlign="center" fontSize="h6.fontSize" fontWeight="fontWeightMedium" color="primary.main" m={1}>
                                <Button
                                  onClick={() => props.handleSelect(parseInt(grid.i, 10))}
                                >
                                  {props.dataMap.get(grid.i).itemCount === 0 ? (
                                    <span>
                                      <PostAdd />
                                      Add items
                                    </span>
                                  ) : (
                                    <span>
                                      <FormatListBulleted />
                                      {props.dataMap.get(grid.i).itemCount}
                                      {' item(s)'}
                                    </span>
                                  )}
                                </Button>
                              </Box>
                            )
                      }

                      {
                        // item tags
                        props.dataMap != null
                        && props.dataMap.get(grid.i) != null
                        && props.dataMap.get(grid.i).itemTags.map((tag, i) => (
                          i === grid.w * (isLargeScreen ? 3 : 1) - 1 ? (
                            // small screen and last displayable tags
                            <span key={`${grid.i}-${tag}`}>
                              <OverlayTrigger
                                placement="right"
                                delay={{ show: 250, hide: 400 }}
                                overlay={prop => renderTagsTooltip(prop, `#${props.dataMap.get(grid.i).itemTags.slice(i).join(', #')}`)}
                              >
                                <Badge variant="success">
                                  {props.dataMap.get(grid.i).itemTags.length - i}
                                  + tags
                                </Badge>
                              </OverlayTrigger>

                            </span>
                          ) : i >= grid.w * (isLargeScreen ? 3 : 1) ? null : (
                            // large screen + small screen < grid width
                            <span key={`${grid.i}-${tag}`}>
                              <Badge variant="warning">
                                #
                                {tag}
                              </Badge>
                              {' '}
                            </span>
                          )
                        ))
                      }
                      {
                        // prevent delete failure when grid contains items inside
                        // show delete grid button only if read only mode
                        // and new grid OR old grid without any item inside
                        props.currMode === Constants.FORM_READONLY_MODE // under edit mode
                        && (
                          parseInt(grid.i, 10) < 0 // new grid, not yet save
                          || (
                            props.dataMap != null && props.dataMap.get(grid.i) != null // old grid, no item in grid
                            && props.dataMap.get(grid.i).itemCount === 0
                          )
                        )
                          ? (
                            <Box
                              position="absolute"
                              zIndex="tooltip"
                            >
                              <IconButton
                                aria-label="delete"
                                onClick={() => props.handleRemove(grid.i)}
                              >
                                <Delete />
                              </IconButton>
                            </Box>
                          ) : null
                      }

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
  displayMsg: PropTypes.oneOfType([PropTypes.object]).isRequired,
  pageLoading: PropTypes.bool.isRequired,
  tempLayouts: PropTypes.arrayOf(PropTypes.object).isRequired,
  dataMap: PropTypes.oneOfType([PropTypes.object]).isRequired,
  isDirtyWrite: PropTypes.bool.isRequired,
  currMode: PropTypes.string.isRequired,
  gridImgPath: PropTypes.string,
  handleNew: PropTypes.func.isRequired,
  handleToggleMode: PropTypes.func.isRequired,
  handleSave: PropTypes.func.isRequired,
  handleCancel: PropTypes.func.isRequired,
  handleUpdateLayout: PropTypes.func.isRequired,
  handleRemove: PropTypes.func.isRequired,
  handleSelect: PropTypes.func.isRequired,
  handleGoBack: PropTypes.func.isRequired
};

export default GridComp;
